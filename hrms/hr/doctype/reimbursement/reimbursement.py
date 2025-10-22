# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate


class Reimbursement(Document):
	def on_submit(self):
		if self.status == "Approved":
			self.update_employee_reimbursement()
			# self.create_additional_salary()
	
	def update_employee_reimbursement(self):
		employee = frappe.get_doc("Employee", self.employee)

		total_reimbursement = employee.total_reimbursement or 0
		reimbursement_used = employee.reimbursement_used or 0

		reimbursement_used += self.amount
		balance = total_reimbursement - reimbursement_used

		employee.reimbursement_used = reimbursement_used
		employee.balance = balance
		employee.save(ignore_permissions=True)

