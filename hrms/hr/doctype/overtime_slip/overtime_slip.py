# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_months, get_first_day, get_last_day, getdate


class OvertimeSlip(Document):
	MAX_MONTHLY_OVERTIME = 72

	def before_save(self):
		self.create_overtime_record()
		self.check_overtime_hours()
	
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

		# self.calculates = []
		existing = {d.overtime_calculation for d in self.overtime_summary}
		total_hours = 0
		total_amount = 0

		for c in calculates:
			if c.name not in existing:
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

	def check_overtime_hours(self):
		if self.total_hours > self.MAX_MONTHLY_OVERTIME:
			excesses = self.total_hours - self.MAX_MONTHLY_OVERTIME

			frappe.msgprint(f"Total Overtime Hours is more than {self.MAX_MONTHLY_OVERTIME}. ")

			self.total_hours = self.MAX_MONTHLY_OVERTIME

			from_date = getdate(self.from_date)
			next_from_date = None
			next_to_date = None

			if from_date.day >= 21:
				next_from_date = add_months(from_date, 1).replace(day=21)
				next_to_date = add_months(from_date, 2).replace(day=20)
			else:
				next_from_date = from_date.replace(day=21)
				next_to_date = add_months(from_date, 1).replace(day=20)

			next_slip = frappe.new_doc("Overtime Slip")
			next_slip.employee = self.employee
			next_slip.from_date = next_from_date
			next_slip.to_date = next_to_date
			next_slip.total_hours = excesses
			next_slip.total_amount = 0
			next_slip.status = "Draft"
			next_slip.insert(ignore_permissions=True)

			frappe.msgprint(f"Overtime {excesses} hours automatically move on the next month.")

# @frappe.whitelist()
# def get_total_overtime(employee, start_date, end_date):
#     """Ambil total lembur pegawai untuk rentang tanggal tertentu"""
#     res = frappe.db.sql("""
#         SELECT SUM(total_amount)
#         FROM `tabOvertime Slip`
#         WHERE employee = %s
#         AND docstatus = 1
#         AND (
#             (from_date BETWEEN %s AND %s)
#             OR (to_date BETWEEN %s AND %s)
#         )
#     """, (employee, start_date, end_date, start_date, end_date))

#     return float(res[0][0]) if res and res[0][0] else 0.0

