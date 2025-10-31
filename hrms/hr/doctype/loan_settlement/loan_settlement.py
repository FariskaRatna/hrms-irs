# Copyright (c) 2025
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LoanSettlement(Document):
    def validate(self):
        # Ambil data Employee dan Loan Application
        if not self.loan_application:
            frappe.throw("Please select a Loan Application")

        loan = frappe.get_doc("Loan Application", self.loan_application)
        employee = frappe.get_doc("Employee", self.employee)

        # Ambil saldo awal
        self.total_balance = (employee.loan_balance or 0) - (self.amount or 0)

        if self.total_balance < 0:
            frappe.throw("Payment amount exceeds remaining loan balance")

    def on_submit(self):
        # Update saldo di Employee
        employee = frappe.get_doc("Employee", self.employee)
        employee.loan_balance = (employee.loan_balance or 0) - (self.amount or 0)
        employee.save(ignore_permissions=True)

        # Update Loan Application (opsional)
        loan = frappe.get_doc("Loan Application", self.loan_application)
        if employee.loan_balance <= 0:
            loan.status = "Settled"
            frappe.msgprint(f"Loan {loan.name} has been fully settled.")
        loan.save(ignore_permissions=True)
