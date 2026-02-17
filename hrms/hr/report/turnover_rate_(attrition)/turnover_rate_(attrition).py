# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql(f"""
		select
			year(relieving_date) as year,
			count(*) as leavers,
			(
				select count(*)
				from `tabEmployee` emp2
				where emp2.date_of_joining <= last_day(concat(year(emp1.relieving_date), '-12-31'))
			) as total_employees
		from `tabEmployee` emp1
		where
			status = 'Left'
			and relieving_date is not null
		group by year
		order by year
	""", as_dict=True)

	for d in data:
		if d.total_employees:
			d.turnover_rate = round((d.leavers / d.total_employees) * 100, 2)
		else:
			d.turnover_rate = 0

	columns = [
		{"label": "Year", "fieldname": "year", "fieldtype": "Int", "width": 120},
		{"label": "Leavers", "fieldname": "leavers", "fieldtype": "Int", "width": 120},
		{"label": "Total Employees", "fieldname": "total_employees", "fieldtype": "Int", "width": 160},
		{"label": "Turnover Rate (%)", "fieldname": "turnover_rate", "fieldtype": "Float", "width": 160},
	]

	labels = [str(d.year) for d in data]
	turnover = [d.turnover_rate for d in data]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Turnover Rate (%)",
					"values": turnover
				}
			]
		},
		"type": "bar",
	}

	return columns, data, None, chart
