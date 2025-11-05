# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OvertimeSlip(Document):
	def before_save(self):
		self.create_overtime_record()
	
	def create_overtime_record(self):
		calculates = frappe.get_all(
			"Overtime Calculation",
			filters={
				"employee": self.employee,
				"date": ["between", [self.from_date, self.to_date]],
				"docstatus": 1,
			},
			fields=["name", "date", "day_type", "total_hours", "total_amount"]
		)

		self.calculates = []
		total_hours = 0
		total_amount = 0

		for c in calculates:
			row = self.append("overtime_summary", {})
			row.overtime_calculation = c.name
			row.date = c.date
			row.day_type = c.day_type
			row.total_hours = c.total_hours
			row.amount = c.total_amount
			total_hours += c.total_hours or 0
			total_amount += c.total_amount or 0

		self.total_hours = total_hours
		self.total_amount = total_amount
