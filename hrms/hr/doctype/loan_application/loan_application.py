# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_months, getdate


class LoanApplication(Document):
	def before_submit(self):
		self.set_deduction_start_date()

	def on_submit(self):
		if self.status == "Approved":
			self.update_employee_loan_application()
			self.create_loan_record()
	
	def set_deduction_start_date(self):
		posting_day = getdate(self.posting_date).day
		posting_month = getdate(self.posting_date).month
		posting_year = getdate(self.posting_date).year

		if posting_day <= 15:
			self.deduction_start_date = getdate(f"{posting_year}-{posting_month}-27")
		else:
			next_month_date = add_months(getdate(self.posting_date), 1)
			self.deduction_start_date = getdate(f"{next_month_date.year}-{next_month_date.month}-27")

		
	def update_employee_loan_application(self):
		employee = frappe.get_doc("Employee", self.employee)

		total_loan = employee.total_loan or 0
		total_installment = employee.installment or 0
		loan_balance = employee.loan_balance or 0

		total_loan += self.total_loan
		total_installment += self.installment
		loan_balance += self.total_loan

		employee.total_loan = total_loan
		employee.installment = total_installment
		employee.loan_balance = loan_balance
		employee.save(ignore_permissions=True)

		frappe.msgprint(f"Loan approved for {employee.employee_name}. Deduction starts at {self.deduction_start_date}")
	
	def create_loan_record(self):
		existing_loan = frappe.db.exists("Loan", {"loan_application": self.name})
		if existing_loan:
			frappe,msgprint("Loan record already exists for this Loan Application.")
			return

		loan_doc = frappe.new_doc("Loan")
		loan_doc.employee = self.employee
		loan_doc.loan_application = self.name
		loan_doc.total_loan = self.total_loan
		loan_doc.deduction_start_date = self.deduction_start_date
		loan_doc.installment = self.installment
		loan_doc.total_installments = 12
		loan_doc.paid_installments = 0
		loan_doc.balance_amount = self.total_loan
		loan_doc.repayment_status = "Unpaid"
		loan_doc.status = "Active"

		loan_doc.insert(ignore_permissions=True)
		frappe.msgprint(f"Loan record {loan_doc.name} created for Employee {self.employee}.")