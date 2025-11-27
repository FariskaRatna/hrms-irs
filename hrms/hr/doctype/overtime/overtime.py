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

	def on_submit(self):
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
		calculation.approval_status = "Pending"
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