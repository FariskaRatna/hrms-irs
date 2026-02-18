# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import date
from dateutil.relativedelta import relativedelta

def execute(filters=None):
	today = date.today().replace(day=1)
	start = today - relativedelta(months=11)

	payroll_map = {}

	rows = frappe.db.sql(f"""
		select
			date_format(end_date, '%%Y-%%m') as ym,
			sum(net_pay) as total
		from `tabSalary Slip`
		where end_date >= %s
		and docstatus = 1
		group by ym
		order by ym
	""", (start), as_dict=True)

	for r in rows:
		payroll_map[r.ym] = r.total

	labels = []
	values = []
	data = []

	cursor = start
	for i in range(12):
		ym = cursor.strftime("%Y-%m")
		label = cursor.strftime("%b %Y")

		value = payroll_map.get(ym, 0)

		labels.append(label)
		values.append(value)

		data.append({
			"month": label,
			"payroll": value
		})

		cursor += relativedelta(months=1)

	columns = [
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
		{"label": "Payroll", "fieldname": "payroll", "fieldtype": "Currency", "width": 180},
	]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Payroll",
					"values": values
				}
			]
		},
		"type": "line"
	}

	return columns, data, None, chart
