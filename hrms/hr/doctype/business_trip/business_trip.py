# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_fullname
from hrms.utils import get_employee_email
from frappe import _


class BusinessTrip(Document):
	def before_save(self):
		if self.from_date and self.to_date:
			start = getdate(self.from_date)
			end = getdate(self.to_date)

			days_accumulation = (end - start).days + 1
			self.total_days = days_accumulation

	def on_update(self):
		if self.approval_status == "Open" and self.docstatus < 1:
			if frappe.db.get_single_value("HR Settings", "send_business_trip_notification"):
				self.notify_project_manager()

		elif self.approval_status in ["Approved", "Rejected"] and self.docstatus < 1:
			if frappe.db.get_single_value("HR Settings", "send_business_trip_notification"):
				self.notify_hrd()
				self.notify_employee(sender_email=self.get_email_pm())

	def on_cancel(self):
		if frappe.db.get_single_value("HR Setttings", "send_business_trip_notification"):
			self.notify_employee()

	def on_submit(self):
		if frappe.db.get_single_value("HR Settings", "send_business_trip_notification"):
			self.notify_employee()
			if self.approval_status == "Approved":
				self.create_business_trip_allowance()


	def create_business_trip_allowance(self):
		existing_business_trip = frappe.db.exists("Business Trip Allowance", {"business_trip": self.name})
		if existing_business_trip:
			frappe.msgprint("Business Trip Allowance already  exists for this Business Trip")
			return

		bt_doc = frappe.new_doc("Business Trip Allowance")
		bt_doc.employee = self.employee
		bt_doc.business_trip = self.name
		# bt_doc.business_trip_allowance_type = self.business_trip_type
		bt_doc.destination = self.destination
		bt_doc.departure_date = self.from_date
		bt_doc.return_date = self.to_date
		bt_doc.total_days = self.total_days
		bt_doc.allowance_amount = 0
		bt_doc.status = "Draft"

		bt_doc.insert(ignore_permissions=True)
		frappe.msgprint(f"Business Trip Allowance {bt_doc.name} created for Employee {self.employee}.")

	def get_requester(self):
		user_id = frappe.db.get_value("Employee", self.employee, "user_id") or self.owner
		return frappe.get_value("User", user_id, "email")
	
	def get_email_pm(self):
		if self.pm_user:
			frappe.get_value("User", self.pm_user, "email")
		return None
	
	def get_email_hr(self):
		if self.hrd_user:
			frappe.get_value("User", self.hrd_user, "email")
		return None

	def notify_project_manager(self):
		if self.pm_user:
			parent_doc = frappe.get_doc("Business Trip", self.name)
			args = parent_doc.as_dict()

			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Business Trip Request from {self.employee_name} Requires Your Approval",
				"email_content": f"Employee {self.employee_name} has submitted an business trip request.",
				"for_user": self.pm_user,
				"type": "Alert",
				"document_type": "Business Trip",
				"document_name": self.name
			}).insert(ignore_permissions=True)

			template = frappe.db.get_single_value("HR Settings", "business_trip_application_notification_template")
			if not template:
				frappe.msgprint(_("Please set default template for Business Trip Application in HR Settings."))
				return
			email_template = frappe.get_doc("Email Template", template)
			subject = frappe.render_template(email_template.subject, args)
			message = frappe.render_template(email_template.response_, args)

			self.notify(
				{
					"message": message,
					"message_to": self.pm_user,
					"subject": subject,
					"sender_email": self.get_requester(),
				}
			)

	def notify(self, args):
		args = frappe._dict(args)
		contact = args.message_to
		if not isinstance(contact, list):
			if args.get("notify") != "employee":
				contact = frappe.get_doc("User", contact).email or contact

		sender_email = args.get("sender_email")
		if not sender_email:
			sender_email = frappe.get_doc("User", frappe.session.user).email

		# sender = dict()
		# sender["email"] = frappe.get_doc("User", frappe.session.user).email
		# sender["full_name"] = get_fullname(sender["email"])

		try:
			frappe.sendmail(
				recipients=contact,
				sender=sender_email,
				subject=args.subject,
				message=args.message,
			)
			frappe.msgprint(_("Email sent to {0}").format(contact))
		except frappe.OutgoingEmailError:
			pass
	
	def notify_employee(self, sender_email=None):
		employee_email = get_employee_email(self.employee)

		if not employee_email:
			return

		employee_user = frappe.db.get_value("Employee", self.employee, "user_id")

		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": f"Business Trip Request {self.approval_status}",
			"email_content": f"Your business trip request has been {self.approval_status}.",
			"for_user": employee_user,
			"type": "Alert",
			"document_type": "Business Trip",
			"document_name": self.name
		}).insert(ignore_permissions=True)
		
		parent_doc = frappe.get_doc("Business Trip", self.name)
		args = parent_doc.as_dict()

		template = frappe.db.get_single_value("HR Settings", "business_trip_status_notification_template")
		if not template:
			frappe.msgprint(_("Please set default template for Business Trip Status Notification in HR Settings."))
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

	def notify_hrd(self):
		if self.hrd_user:
			parent_doc = frappe.get_doc("Business Trip", self.name)
			args = parent_doc.as_dict()

			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Business Trip Request {self.employee_name} has been Processed by Lead",
				"email_content": f"Employee {self.employee_name} submitted business trip and Lead has been processed.",
				"for_user": self.hrd_user,
				"type": "Alert",
				"document_type": "Business Trip",
				"document_name": self.name
			}).insert(ignore_permissions=True)

			template = frappe.db.get_single_value("HR Settings", "business_trip_application_hr_template")
			if not template:
				frappe.msgprint(_("Please set default tempalte for Business Trip Application Notification fo HRD in HR Settings."))
				return
			email_template = frappe.get_doc("Email Template", template)
			subject = frappe.render_template(email_template.subject, args)
			message = frappe.render_template(email_template.response_, args)

		self.notify(
			{
				"message": message,
				"message_to": self.hrd_user,
				"subject": subject,
				"sender_email": self.get_requester(),
			}
		)


@frappe.whitelist()
def get_pm_user(employee):
	pm_user, department = frappe.db.get_value("Employee", employee, ["project_manager", "department"])

	if not pm_user and department:
		pm_user = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "leave_approvers", "idx": 1},
			"approver",
		)

	return pm_user

