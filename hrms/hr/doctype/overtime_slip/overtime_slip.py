# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_months, get_first_day, get_last_day, getdate


class OvertimeSlip(Document):
	MAX_MONTHLY_OVERTIME = 72

	def before_save(self):
		self.create_overtime_record()
		self.split_overtime()

	def before_insert(self):
		self.apply_previous_overtime()
	
	def create_overtime_record(self):
		calculates = frappe.get_all(
			"Overtime Calculation",
			filters={
				"employee": self.employee,
				"date": ["between", [self.from_date, self.to_date]],
				"approval_status": "Approved",
			},
			fields=["name", "date", "day_type", "total_hours", "total_amount"]
		)

		# self.calculates = []
		existing = {d.overtime_calculation for d in self.overtime_summary}
		self.calculation_buffer = calculates
		# total_hours = 0
		# total_amount = 0

		for c in calculates:
			if c.name not in existing:
				row = self.append("overtime_summary", {})
				row.overtime_calculation = c.name
				row.date = c.date
				row.day_type = c.day_type
				row.total_hours = c.total_hours
				row.amount = c.total_amount
				
		# 	total_hours += c.total_hours or 0
		# 	total_amount += c.total_amount or 0

		# self.total_hours = total_hours
		# self.total_amount = total_amount

	def split_overtime(self):
		total_used = 0
		next_month_overtime = []

		self.total_hours = 0
		self.total_amount = 0

		for item in self.overtime_summary:
			hours =  item.total_hours or 0

			if total_used + hours <= self.MAX_MONTHLY_OVERTIME:
				self.total_hours += hours
				item.amount = self.calculate_amount(hours, item.day_type)
				self.total_amount += item.amount
				total_used += hours
			else:
				remaining_allowance = max(0, self.MAX_MONTHLY_OVERTIME - total_used)
				excess = hours - remaining_allowance

				if remaining_allowance > 0:
					item.amount = self.calculate_amount(remaining_allowance, item.day_type)
					self.total_amount += item.amount
					self.total_hours += remaining_allowance
					total_used += remaining_allowance

				next_month_overtime.append({
					"hours": excess,
					"day_type": item.day_type
				})

		if next_month_overtime:
			self.create_next_month_slip(next_month_overtime)

	def calculate_amount(self, hours, day_type):
		calc = frappe.new_doc("Overtime Calculation")
		calc.employee = self.employee
		calc.total_hours = hours
		calc.day_type = day_type

		calc.calculate_overtime_pay()
		return calc.total_amount
	
	def create_next_month_slip(self, data):
		next_slip = frappe.new_doc("Overtime Slip")
		next_slip.employee = self.employee
		next_slip.from_date = add_months(getdate(self.from_date), 1).replace(day=21)
		next_slip.to_date = add_months(getdate(self.to_date), 1).replace(day=20)

		total_next_hours = 0
		total_next_amount = 0

		for d in data:
			next_hours = d["hours"]
			next_type = d["day_type"]

			amount = self.calculate_amount(next_hours, next_type)

			total_next_hours += next_hours
			total_next_amount += amount

		next_slip.total_hours = total_next_hours
		next_slip.total_amount = total_next_amount
		next_slip.excess_from_reference = self.name

		next_slip.insert(ignore_permissions=True)
		frappe.msgprint(f"Excess {total_next_hours} hours moved to next month.")



	def check_overtime_hours(self):
		if self.total_hours > self.MAX_MONTHLY_OVERTIME:
			excesses = self.total_hours - self.MAX_MONTHLY_OVERTIME

			frappe.msgprint(f"Total Overtime Hours is more than {self.MAX_MONTHLY_OVERTIME}. ")

			self.total_hours = self.MAX_MONTHLY_OVERTIME
			self.excess_hours = excesses

			# from_date = getdate(self.from_date)
			# next_from_date = None
			# next_to_date = None

			# if from_date.day >= 21:
			# 	next_from_date = add_months(from_date, 1).replace(day=21)
			# 	next_to_date = add_months(from_date, 2).replace(day=20)
			# else:
			# 	next_from_date = from_date.replace(day=21)
			# 	next_to_date = add_months(from_date, 1).replace(day=20)

			# next_slip = frappe.new_doc("Overtime Slip")
			# next_slip.employee = self.employee
			# next_slip.from_date = next_from_date
			# next_slip.to_date = next_to_date
			# next_slip.total_hours = excesses
			# next_slip.total_amount = 0
			# next_slip.status = "Draft"
			# next_slip.insert(ignore_permissions=True)

			frappe.msgprint(f"Overtime {excesses} hours automatically move on the next month.")

	def apply_previous_overtime(self):
		previous = frappe.db.sql("""
			SELECT name, total_hours, total_amount
			FROM `tabOvertime Slip`
			WHERE employee = %s AND docstatus = 1 AND excess_hours > 0
			ORDER BY to_date DESC LIMIT 1
		""", (self.employee,), as_dict=True)


		if previous:
			self.total_hours = (self.total_hours or 0) + previous[0].total_hours
			self.total_amount = (self.total_amount or 0) + previous[0].total_amount

			frappe.msgprint(
				f"{previous[0].total_hours} hours of overtime from last month has been applied."
			)


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

