# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_months, getdate, get_fullname
from frappe import _
from hrms.utils import get_employee_email
from hrms.custom.email_token.loan_application_email_token import build_action_url_loan


class LoanApplication(Document):
	def before_submit(self):
		self.set_deduction_start_date()

	def validate(self):
		if self.total_loan and self.total_loan > 10000000:
			frappe.throw(_("Loan amount exceeds the maximum limit of Rp10.000.000"))

		self.validate_no_active_loan()

	def on_update(self):
		if self.approval_status == "Pending" and self.docstatus < 1:
			if frappe.db.get_single_value("HR Settings", "send_loan_application_notification"):
				self.notify_hrd()

		if self.approval_status in ["Approved", "Rejected"] and self.docstatus < 1:
			if frappe.db.get_single_value("HR Settings", "send_loan_application_notification"):
				if getattr(self.flags, "from_email_action", False):
					self.notify_employee(sender_email=self.get_email_hrd())
				else:
					self.notify_employee(sender_email=self.get_email_hrd())

	def on_submit(self):
		if self.approval_status in ["Pending", "Cancelled"]:
			frappe.throw(_("Only Loan Application with approval status 'Approved' and 'Cancelled' can be submitted"))
			
		if frappe.db.get_single_value("HR Settings", "send_loan_application_notification"):
			self.notify_employee()
			if self.approval_status == "Approved":
				self.validate_no_active_loan()
				self.update_employee_loan_application()
				self.create_loan_record()

	def on_cancel(self):
		if frappe.db.get_single_value("HR Settings", "send_loan_application_notification"):
			self.notify_employee()

	def validate_no_active_loan(self):
		if not self.employee:
			return
		
		active_loan = frappe.db.exists(
			"Loan",
			{
				"employee": self.employee,
				"docstatus": 1,
				"status": ["in", ["Active"]]
			}
		)

		if active_loan:
			frappe.throw(
				_("Employee still has an active/unpaid loan ({0}). Please settle it before applying for a new loan.")
				.format(active_loan)
			)
	
	def set_deduction_start_date(self):
		posting_day = getdate(self.posting_date).day
		posting_month = getdate(self.posting_date).month
		posting_year = getdate(self.posting_date).year

		if posting_day <= 15:
			self.deduction_start_date = getdate(f"{posting_year}-{posting_month}-27")
		else:
			next_month_date = add_months(getdate(self.posting_date), 1)
			self.deduction_start_date = getdate(f"{next_month_date.year}-{next_month_date.month}-27")

		
	def update_employee_loan_application(self):
		employee = frappe.get_doc("Employee", self.employee)

		total_loan = employee.total_loan or 0
		total_installment = employee.installment or 0
		loan_balance = employee.loan_balance or 0

		total_loan += self.total_loan
		total_installment += self.installment
		loan_balance += self.total_loan

		employee.total_loan = total_loan
		employee.installment = total_installment
		employee.loan_balance = loan_balance
		employee.save(ignore_permissions=True)

		frappe.msgprint(_("Loan approved for {0}. Deduction starts at {1}").format(employee.employee_name, self.deduction_start_date))
	
	def create_loan_record(self):
		existing_loan = frappe.db.exists("Loan", {"loan_application": self.name})
		if existing_loan:
			frappe.msgprint("Loan record already exists for this Loan Application.")
			return

		loan_doc = frappe.new_doc("Loan")
		loan_doc.employee = self.employee
		loan_doc.loan_application = self.name
		loan_doc.total_loan = self.total_loan
		loan_doc.deduction_start_date = self.deduction_start_date
		loan_doc.installment = self.installment
		loan_doc.total_installments = 12
		loan_doc.paid_installments = 0
		loan_doc.balance_amount = self.total_loan
		loan_doc.repayment_status = "Unpaid"
		loan_doc.status = "Active"


		loan_doc.insert(ignore_permissions=True)
		frappe.msgprint(_("Loan record {0} created for Employee {1}.").format(loan_doc.name, self.employee_name))

	
	def get_requester(self):
		user_id = frappe.db.get_value("Employee", self.employee, "user_id") or self.owner
		return frappe.get_value("User", user_id, "email")

	def get_email_hrd(self):
		if self.hrd_user:
			return frappe.get_value("User", self.hrd_user, "email")
		return None

	def notify_hrd(self):
		if not self.hrd_user:
			return
		
		parent_doc = frappe.get_doc("Loan Application", self.name)
		approver_user = self.hrd_user or parent_doc.owner
		args = parent_doc.as_dict()

		args.update({
			"approve_url": build_action_url_loan(
				parent_doc.name,
				"Approved",
				approver_user
			),
			"reject_url": build_action_url_loan(
				parent_doc.name,
				"Rejected",
				approver_user
			),
		})

		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": f"Loan Application Request {self.employee_name} Requires Your Approval",
			"email_content": f"Employee {self.employee_name} submitted loan application and requires your approval.",
			"for_user": self.hrd_user,
			"type": "Alert",
			"document_type": "Loan Application",
			"document_name": self.name
		}).insert(ignore_permissions=True)

		template = frappe.db.get_single_value("HR Settings", "loan_request_notification_template")
		if not template:
			frappe.msgprint(_("Please set default template for Loan Application Request Notification in HR Settings."))
			return
		email_template = frappe.get_doc("Email Template", template)
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response_, args)

		self.notify(
			{
				"message": message,
				"message_to": self.hrd_user,
				"subject": subject,
				"sender_email": self.get_requester()
			}
		)


	def notify_employee(self, sender_email=None):
		employee_email = get_employee_email(self.employee)

		if not employee_email:
			return

		employee_user = frappe.db.get_value("Employee", self.employee, "user_id")

		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": f"Loan Application Request {self.approval_status}",
			"email_content": f"Your loan application request has been {self.approval_status}.",
			"for_user": employee_user,
			"type": "Alert",
			"document_type": "Loan Application",
			"document_name": self.name
		}).insert(ignore_permissions=True)
		
		parent_doc = frappe.get_doc("Loan Application", self.name)
		args = parent_doc.as_dict()

		template = frappe.db.get_single_value("HR Settings", "loan_status_notification_template")
		if not template:
			frappe.msgprint(_("Please set default template for Loan Application Status Notification in HR Settings."))
			return
		email_template = frappe.get_doc("Email Template", template)
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response_, args)

		self.notify(
			{
				"message": message,
				"message_to": employee_email,
				"subject": subject,
				"notify": "employee",
				"sender_email": sender_email,
			}
		)
	
	def notify(self, args):
		args = frappe._dict(args)
		contact = args.message_to
		if not isinstance(contact, list):
			if not args.notify == "employee":
				contact = frappe.get_doc("User", contact).email or contact

		sender_email = args.get("sender_email")
		if not sender_email:
			sender_email = frappe.get_doc("User", frappe.session.user).email

		try:
			frappe.sendmail(
				recipients=contact,
				sender=sender_email,
				subject=args.subject,
				message=args.message,
			)
			frappe.msgprint(_("Email sent to {0}").format(contact))
		except frappe.OngoingEmailError:
			pass