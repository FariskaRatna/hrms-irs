# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime


class Overtime(Document):
	def before_save(self):
		if self.start_time and self.end_time:
			fmt = "%H:%M:%S"
			start = datetime.strptime(str(self.start_time), fmt)
			end = datetime.strptime(str(self.end_time), fmt)
			diff = (end - start).seconds / 3600
			self.total_hours = round(diff, 2)

	def on_submit(self):
		if self.status == "Approved":
			self.create_overtime_slip()

	def create_overtime_slip(self):
		existing_slip = frappe.db.exists("Overtime Slip", {"reference_request": self.name})
		if existing_slip:
			frappe.msgprint("Overtime Slip already exists for this Overtime Request.")
			return
		
		day_type = "Weekend" if self.is_weekend() else "Weekday"

		slip = frappe.new_doc("Overtime Slip")
		slip.employee = self.employee
		slip.date = self.date
		slip.total_hours = self.total_hours
		slip.day_type = day_type
		slip.reference_request = self.name
		slip.status = "Pending"
		slip.insert(ignore_permissions=True)
		frappe.msgprint(f"Overtime Slip for {self.employee} successfully created.")
	
	def is_weekend(self):
		if not self.date:
			return False
		# ubah dari string ke datetime
		date_obj = datetime.strptime(str(self.date), "%Y-%m-%d").date()
		# .weekday() -> 5 = Sabtu, 6 = Minggu
		return date_obj.weekday() in (5, 6)