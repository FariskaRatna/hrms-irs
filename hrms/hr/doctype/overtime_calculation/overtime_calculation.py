# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OvertimeCalculation(Document):
	def before_save(self):
		self.calculate_overtime_pay()
	
	def on_submit(self):
		if self.status == "Approved":
			self.create_overtime_record()
	
	def calculate_overtime_pay(self):
		employee = frappe.get_doc("Employee", self.employee)

		assignment = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": self.employee, "docstatus": 1},
			fields = ["base", "salary_structure"],
			limit = 1
		)
		# base_salary = getattr(employee, "basic_salary", None) or getattr(employee, "base", 0) or 0
		base_salary = assignment[0].base if assignment else 0

		hourly_rate = base_salary / 173 if base_salary else 0
		total_hours = self.total_hours or 0
		total_coef = 0

		if self.day_type == "Weekday":
			if total_hours > 0:
				total_coef += 1.5
			if total_hours > 1:
				total_coef += (total_hours - 1) * 2
		elif self.day_type == "Weekend":
			if total_hours <= 8:
				total_coef += total_hours * 2
			elif total_hours == 9:
				total_coef += (8 *2) + 3
			elif total_hours > 9:
				total_coef += (8 * 2) + 3 + (total_hours - 9) * 4

		self.total_amount = total_coef * hourly_rate if total_coef > 0 else 0

	def create_overtime_record(self):
		existing_overtime = frappe.db.exists("Overtime Calculation", {"reference_request": self.name})
		if existing_overtime:
			frappe.msgprint("Overtime record already exists for Overtime Application.")
			return
		overtime_doc = frappe.new_doc
