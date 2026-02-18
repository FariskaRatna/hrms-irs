# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from collections import defaultdict

def execute(filters=None):

	rows = frappe.db.sql("""
		SELECT
			YEAR(ss.end_date) as year,
			MONTH(ss.end_date) as month,
			e.department,
			SUM(ss.net_pay) as payroll
		FROM `tabSalary Slip` ss
		LEFT JOIN `tabEmployee` e ON e.name = ss.employee
		WHERE ss.docstatus = 1
		GROUP BY YEAR(ss.end_date), MONTH(ss.end_date), e.department
		ORDER BY YEAR(ss.end_date), MONTH(ss.end_date)
	""", as_dict=True)


	month_order = []
	month_label_map = {}
	dept_map = defaultdict(lambda: defaultdict(float))
	month_total_map = defaultdict(float)
	departments = set()

	for r in rows:
		year = r.year
		month = r.month
		dept = r.department or "No Department"
		pay = r.payroll or 0

		month_key = f"{year}-{month:02d}"
		month_label = f"{month:02d}-{str(year)[-2:]}"   

		if month_key not in month_order:
			month_order.append(month_key)
			month_label_map[month_key] = month_label

		dept_map[dept][month_key] += pay
		month_total_map[month_key] += pay
		departments.add(dept)


	data = []
	for m in month_order:
		data.append({
			"month": month_label_map[m],
			"total_payroll": month_total_map[m]
		})


	columns = [
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
		{"label": "Total Payroll", "fieldname": "total_payroll", "fieldtype": "Currency", "width": 200},
	]


	datasets = []
	for dept in sorted(departments):
		values = [dept_map[dept].get(m, 0) for m in month_order]

		datasets.append({
			"name": dept,
			"values": values
		})


	chart = {
		"data": {
			"labels": [month_label_map[m] for m in month_order],
			"datasets": datasets
		},
		"type": "bar",
		# "barOptions": {"stacked": True}
	}

	return columns, data, None, chart
