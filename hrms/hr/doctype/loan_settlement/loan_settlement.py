# Copyright (c) 2025
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LoanSettlement(Document):
    def validate(self):
        if not self.loan:
            frappe.throw("Please select a Loan")

        loan = frappe.get_doc("Loan", self.loan)
        employee = frappe.get_doc("Employee", self.employee)

        new_balance = (loan.balance_amount or 0) - (self.amount or 0)

        if new_balance < 0:
            frappe.throw("Payment amount exceeds remaining loan balance")

        self.remaining_balance = new_balance

    def on_submit(self):
        loan = frappe.get_doc("Loan", self.loan)
        employee = frappe.get_doc("Employee", self.employee)

        loan.balance_amount = (loan.balance_amount or 0) - (self.amount or 0)

        if loan.installment and self.amount >= loan.installment:
            loan.paid_installments += int(self.amount / loan.installment)

        if loan.balance_amount <= 0:
            loan.repayment_status = "Paid"
            loan.status = "Closed"
            frappe.msgprint(f"Loan {loan.name} has been fully settled.")
        else:
            frappe.msgprint(f"Loan {loan.name} has been partially settled. Remaining balance: {loan.balance_amount}")

        repayment = loan.append("repayment_tracking", {})
        repayment.payment_date = self.settlement_date
        repayment.amount_paid = self.amount
        repayment.balance_after = loan.balance_amount
        repayment.reference = self.name
        repayment.remarks = "Loan Settlement Payment"
        
        loan.save(ignore_permissions=True)

        # Update saldo di Employee
        employee.loan_balance = (employee.loan_balance or 0) - (self.amount or 0)
        if employee.loan_balance < 0:
            employee.loan_balance = 0
        employee.save(ignore_permissions=True)
