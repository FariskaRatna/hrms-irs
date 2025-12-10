# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe import _
from frappe.utils import get_fullname
from hrms.utils import get_employee_email


class Overtime(Document):
	def before_save(self):
		if self.start_time and self.end_time:
			fmt = "%H:%M:%S"
			start = datetime.strptime(str(self.start_time), fmt)
			end = datetime.strptime(str(self.end_time), fmt)
			diff = (end - start).seconds / 3600

			full_hour = int(diff)
			remainder = diff - full_hour

			if remainder >= 0.75:
				rounding = 1.0
			elif remainder >= 0.25:
				rounding = 0.5
			else:
				rounding = 0.0

			total_hour = full_hour + rounding
			self.total_hours = round(total_hour, 2)

	def on_update(self):
		if self.approval_status == "Pending" and self.docstatus < 1:
			if frappe.db.get_single_value("HR Settings", "send_overtime_application_notification"):
				self.notify_assigned_by()

		if self.approval_status in ["Approved", "Rejected"] and self.docstatus < 1:
			if frappe.db.get_single_value("HR Settings", "send_overtime_application_notification"):
				self.notify_assigned_by()
				self.notify_project_manager()
				self.notify_employee(sender_email=self.get_email_assigned_by())


	def on_cancel(self):
		if frappe.db.get_single_value("HR Settings", "send_overtime_application_notification"):
			self.notify_employee()

	def on_submit(self):
		if frappe.db.get_single_value("HR Settings", "send_overtime_application_notification"):
			self.notify_employee()
			if self.approval_status == "Approved":
				self.create_overtime_calculation()
				# self.create_overtime_summary()

	def create_overtime_calculation(self):
		existing_calculation = frappe.db.exists("Overtime Calculation", {"reference_request": self.name})
		if existing_calculation:
			frappe.msgprint("Overtime calculation already exists for this Overtime Request.")
			return
		
		day_type = "Weekend" if self.is_weekend() else "Weekday"

		calculation = frappe.new_doc("Overtime Calculation")
		calculation.employee = self.employee
		calculation.date = self.date
		calculation.total_hours = self.total_hours
		calculation.day_type = day_type
		calculation.reference_request = self.name
		calculation.approval_status = "Approved"
		calculation.insert(ignore_permissions=True)
		frappe.msgprint(f"Overtime calculation for {self.employee_name} successfully created.")
	
	def is_weekend(self):
		if not self.date:
			return False
		# ubah dari string ke datetime
		date_obj = datetime.strptime(str(self.date), "%Y-%m-%d").date()
		# .weekday() -> 5 = Sabtu, 6 = Minggu
		return date_obj.weekday() in (5, 6)

	# def create_overtime_summary(self):
	# 	overtime_doc = frappe.new_doc("Overtime Slip")
	# 	overtime_doc.employee = self.employee
	# 	overtime_doc.from_date = 0
	# 	overtime_doc.to_date = 0
	# 	overtime_doc.total_hours = 0
	# 	overtime_doc.status = "Draft"

	# 	overtime_doc.insert(ignore_permissions=True)
	# 	frappe.msgprint(f"Overtime record {overtime_doc.name} created for Employee {self.employee}.")

	def get_requester(self):
		user_id = frappe.db.get_value("Employee", self.employee, "user_id") or self.owner
		return frappe.get_value("User", user_id, "email")

	def get_email_pm(self):
		if self.pm_user:
			frappe.get_value("User", self.pm_user, "email")
		return None

	def get_email_assigned_by(self):
		if self.assigned_by:
			return frappe.get_value("User", self.assigned_by, "email")
		return None

	def notify_project_manager(self):
		if self.pm_user:
			parent_doc = frappe.get_doc("Overtime", self.name)
			args = parent_doc.as_dict()

			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Overtime Request {self.employee_name} Requires Your Approval",
				"email_content": f"Employee {self.employee_name} submitted overtime and requires your approval.",
				"for_user": self.pm_user,
				"type": "Alert",
				"document_type": "Overtime",
				"document_name": self.name
			}).insert(ignore_permissions=True)

			template = frappe.db.get_single_value("HR Settings", "overtime_request_notification_lead_template")
			if not template:
				frappe.msgprint(_("Please set default template for Overtime Request Notification in HR Settings."))
				return
			email_template = frappe.get_doc("Email Template", template)
			subject = frappe.render_template(email_template.subject, args)
			message = frappe.render_template(email_template.response_, args)

			self.notify(
				{
					"message": message,
					"message_to": self.pm_user,
					"subject": subject,
					"sender_email": self.get_requester()
				}
			)

	def notify_assigned_by(self):
		if self.assigned_by:
			parent_doc = frappe.get_doc("Overtime", self.name)
			args = parent_doc.as_dict()

			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Overtime Request from {self.employee_name}",
				"email_content": f"Employee {self.employee_name} has submitted an overtime request.",
				"for_user": self.assigned_by,
				"type": "Alert",
				"document_type": "Overtime",
				"document_name": self.name
			}).insert(ignore_permissions=True)

			template = frappe.db.get_single_value("HR Settings", "overtime_request_notification_template")
			if not template:
				frappe.msgprint(_("Please set default template for Overtime Request Notification in HR Settings."))
				return
			email_template = frappe.get_doc("Email Template", template)
			subject = frappe.render_template(email_template.subject, args)
			message = frappe.render_template(email_template.response_, args)

			self.notify(
				{
					"message": message,
					"message_to": self.assigned_by,
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
			"subject": f"Overtime Request {self.approval_status}",
			"email_content": f"Your overtime request has been {self.approval_status}.",
			"for_user": employee_user,
			"type": "Alert",
			"document_type": "Overtime",
			"document_name": self.name
		}).insert(ignore_permissions=True)
		
		parent_doc = frappe.get_doc("Overtime", self.name)
		args = parent_doc.as_dict()

		template = frappe.db.get_single_value("HR Settings", "overtime_status_notification_template")
		if not template:
			frappe.msgprint(_("Please set default template for Overtime Status Notification in HR Settings."))
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