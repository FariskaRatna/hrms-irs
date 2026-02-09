# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_months


class ReimbursementSummary(Document):
	def on_submit(self):
		self.create_reimbursement_report()

	def create_reimbursement_report(self):
		if not self.employee:
			return
		
		start_date = getdate(self.period_start)
		end_date = getdate(self.period_end)

		report = frappe.get_all(
			"Reimbursement Report",
			filters={
				"from_date": start_date,
				"to_date": end_date
			},
			limit=1
		)

		if report:
			report = frappe.get_doc("Reimbursement Report", report[0].name)
		
		else:
			report = frappe.new_doc("Reimbursement Report")
			report.from_date = start_date
			report.to_date = end_date
			
		report.append("reimbursement_report", {
			"employee": self.employee,
			"employee_name": self.employee_name,
			"total_reimbursement": self.total_amount
		})

		report.save(ignore_permissions=True)
