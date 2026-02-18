# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, add_months, get_first_day, get_last_day
from datetime import datetime

def execute(filters=None):
	filters = filters or {}

	if not filters.get("from_date") or not filters.get("to_date"):
		from_date, to_date = get_current_payroll_period()
		filters["from_date"] = from_date
		filters["to_date"] = to_date
	else:
		from_date = filters.get("from_date")
		to_date = filters.get("to_date")

	date_filters = {
		"from_date": from_date,
		"to_date": to_date
	}

	slips = frappe.db.sql("""
		SELECT name, employee, end_date, net_pay
		FROM `tabSalary Slip`
		WHERE end_date BETWEEN %(from_date)s AND %(to_date)s
		AND docstatus = 1
	""", date_filters, as_dict=True)

	payroll = 0
	total_thp = 0

	assignment_cache = {}

	for s in slips:
		payroll += s.net_pay or 0

		if s.employee not in assignment_cache:
			assignment = frappe.db.sql("""
				SELECT base
				FROM `tabSalary Structure Assignment`
				WHERE employee=%s
				AND effective_date <= %s
				ORDER BY effective_date DESC
				LIMIT 1
			""", (s.employee, s.end_date), as_dict=True)

			assignment_cache[s.employee] = assignment[0].base if assignment else 0

		base = assignment_cache[s.employee]

		harian = frappe.db.get_value("Salary Slip", s.name, "harian") or 0

		thp = base + (20 * harian)
		total_thp += thp

	thp = total_thp

	bpjs_tk = thp * 0.057
	bpjs_kes = thp * 0.05
	pensiun = thp * 0.03
	bpjs_total = bpjs_tk + bpjs_kes


	allowance = frappe.db.sql("""
		SELECT SUM(total_allowance)
		FROM `tabBusiness Trip Allowance`
		WHERE departure_date BETWEEN %(from_date)s AND %(to_date)s
		AND docstatus = 1
	""", date_filters)[0][0] or 0


	reimbursement = frappe.db.sql("""
		SELECT SUM(total_amount)
		FROM `tabReimbursement Summary`
		WHERE period_start BETWEEN %(from_date)s AND %(to_date)s
		AND docstatus = 1
	""", date_filters)[0][0] or 0


	loan = frappe.db.sql("""
		SELECT SUM(total_loan)
		FROM `tabLoan Application`
		WHERE date_required BETWEEN %(from_date)s AND %(to_date)s
		AND docstatus = 1
	""", date_filters)[0][0] or 0


	total_hr_cost = payroll + allowance + reimbursement + loan + bpjs_total + pensiun
	non_payroll = allowance + reimbursement + loan

	data = [{
		"month": from_date,
		"total_hr_cost": total_hr_cost,
		"payroll": payroll,
		"non_payroll": non_payroll,
		"bpjs": bpjs_total,
		"pensiun": pensiun
	}]

	columns = [
		{"label": "Period", "fieldname": "month", "fieldtype": "Date", "width": 120},
		{"label": "Total HR Cost", "fieldname": "total_hr_cost", "fieldtype": "Currency", "width": 180},
		{"label": "Payroll", "fieldname": "payroll", "fieldtype": "Currency", "width": 150},
		{"label": "Non Payroll", "fieldname": "non_payroll", "fieldtype": "Currency", "width": 150},
		{"label": "BPJS", "fieldname": "bpjs", "fieldtype": "Currency", "width": 150},
		{"label": "Pensiun", "fieldname": "pensiun", "fieldtype": "Currency", "width": 150},
	]

	chart = {
		"data": {
			"labels": ["Payroll", "Allowance+Reimb+Loan", "BPJS", "Pensiun"],
			"datasets": [{
				"values": [payroll, non_payroll, bpjs_total, pensiun]
			}]
		},
		"type": "donut"
	}

	return columns, data, None, chart


def get_current_payroll_period():
	"""
	Calculate payroll period: 21st of last month to 20th of current month
	
	Examples:
	- Today: Feb 18, 2026 → Period: Jan 21, 2026 to Feb 20, 2026
	- Today: Feb 25, 2026 → Period: Feb 21, 2026 to Mar 20, 2026
	"""
	today = getdate()

	if today.day <= 20:
		from_date = datetime(today.year, today.month, 21)
		from_date = add_months(from_date, -1)
		
		to_date = datetime(today.year, today.month, 20)

	else:
		from_date = datetime(today.year, today.month, 21)

		to_date = datetime(today.year, today.month, 20)
		to_date = add_months(to_date, 1)
	
	return getdate(from_date), getdate(to_date)