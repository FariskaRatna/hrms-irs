# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate


class LoanApplication(Document):
	def on_submit(self):
		if self.status == "Approved":
			self.update_employee_loan_application()
		
	def update_employee_loan_application(self):
		employee = frappe.get_doc("Employee", self.employee)

		total_loan = employee.total_loan or 0
		total_installment = employee.installment or 0

		total_installment += self.total_installment
		balance = total_loan - total_installment

		employee.installment = total_installment
		employee.balance = balance
		employee.save(ignore_permissions=True)
