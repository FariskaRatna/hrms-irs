# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Loan(Document):
	pass


# def custom_validate_loan(doc, method):
# 	if not doc.employee:
# 		frappe.throw("Employee must be specified for the Loan")
# 	if doc.total_loan <= 0:
# 		frappe.throw("Total Loan amount must be greater than zero")
def on_cancel(doc, method):
	clear_employee_loan(doc.employee)

def on_trash(doc, method):
	clear_employee_loan(doc.employee)

def on_update_after_submit(doc, method):
	if doc.repayment_status == "Paid":
		clear_employee_loan(doc.employee)

def clear_employee_loan(employee):
	employee_loan = frappe.get_doc("Employee", employee)

	active_loans = frappe.get_all(
		"Loan",
		filters={"employee": employee, "docstatus": 1, "repayment_status": ["!=", "Paid"]},
		fields=["name"]
	)

	if not active_loans:
		employee_loan.total_loan = 0
		employee_loan.installment = 0
		employee_loan.loan_balance = 0
		employee_loan.save(ignore_permissions=True)
