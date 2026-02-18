# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import date
from dateutil.relativedelta import relativedelta

def execute(filters=None):

	months_back = 6   # last 6 months
	today = date.today().replace(day=1)
	start_month = today - relativedelta(months=months_back-1)

	labels = []
	payroll_vals = []
	non_payroll_vals = []
	bpjs_vals = []
	pensiun_vals = []

	data = []

	for i in range(months_back):

		month_start = start_month + relativedelta(months=i)
		month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)

		label = month_start.strftime("%m-%y")
		labels.append(label)

		# ================= PAYROLL =================
		slips = frappe.db.sql("""
			SELECT name, employee, end_date, net_pay
			FROM `tabSalary Slip`
			WHERE end_date BETWEEN %s AND %s
			AND docstatus = 1
		""", (month_start, month_end), as_dict=True)

		payroll = 0
		total_thp = 0
		assignment_cache = {}

		harian_map = dict(frappe.db.sql("""
			SELECT parent, amount
			FROM `tabSalary Detail`
			WHERE parenttype='Salary Slip'
			AND salary_component='Tunjangan Harian'
		"""))


		for s in slips:
			payroll += s.net_pay or 0

			if s.employee not in assignment_cache:
				base = frappe.db.sql("""
					SELECT base
					FROM `tabSalary Structure Assignment`
					WHERE employee=%s
					AND from_date <= %s
					ORDER BY from_date DESC
					LIMIT 1
				""", (s.employee, s.end_date))

				assignment_cache[s.employee] = base[0][0] if base else 0

			base = assignment_cache[s.employee]
			harian = harian_map.get(s.name, 0)

			thp = base + (20 * harian)
			total_thp += thp


		# ================= NON PAYROLL =================
		allowance = frappe.db.sql("""
			SELECT SUM(total_allowance) FROM `tabBusiness Trip Allowance`
			WHERE departure_date BETWEEN %s AND %s AND docstatus=1
		""", (month_start, month_end))[0][0] or 0

		reimbursement = frappe.db.sql("""
			SELECT SUM(total_amount) FROM `tabReimbursement Summary`
			WHERE period_start BETWEEN %s AND %s AND docstatus=1
		""", (month_start, month_end))[0][0] or 0

		loan = frappe.db.sql("""
			SELECT SUM(total_loan) FROM `tabLoan Application`
			WHERE date_required BETWEEN %s AND %s AND docstatus=1
		""", (month_start, month_end))[0][0] or 0

		non_payroll = allowance + reimbursement + loan

		# ================= BPJS =================
		bpjs = (total_thp * 0.057) + (total_thp * 0.05)
		pensiun = total_thp * 0.03

		# save chart values
		payroll_vals.append(payroll)
		non_payroll_vals.append(non_payroll)
		bpjs_vals.append(bpjs)
		pensiun_vals.append(pensiun)

		data.append({
			"month": label,
			"payroll": payroll,
			"non_payroll": non_payroll,
			"bpjs": bpjs,
			"pensiun": pensiun,
			"total": payroll + non_payroll + bpjs + pensiun
		})

	# ================= TABLE =================
	columns = [
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 90},
		{"label": "Payroll", "fieldname": "payroll", "fieldtype": "Currency", "width": 140},
		{"label": "Non Payroll", "fieldname": "non_payroll", "fieldtype": "Currency", "width": 140},
		{"label": "BPJS", "fieldname": "bpjs", "fieldtype": "Currency", "width": 120},
		{"label": "Pensiun", "fieldname": "pensiun", "fieldtype": "Currency", "width": 120},
		{"label": "Total HR Cost", "fieldname": "total", "fieldtype": "Currency", "width": 160},
	]

	# ================= CHART =================
	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "Payroll", "values": payroll_vals},
				{"name": "Non Payroll", "values": non_payroll_vals},
				{"name": "BPJS", "values": bpjs_vals},
				{"name": "Pensiun", "values": pensiun_vals},
			]
		},
		"type": "bar",
		"barOptions": {"stacked": True}
	}

	return columns, data, None, chart
