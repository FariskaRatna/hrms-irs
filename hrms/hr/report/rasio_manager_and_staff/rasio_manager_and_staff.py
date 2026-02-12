# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql(f"""
		select
			designation,
			count(name) as total_employees
		from `tabEmployee`
		where status = 'Active'
		group by designation
		order by designation
	""", as_dict=True)

	columns = [
		{"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 180},
		{"label": "Total Employees", "fieldname": "total_employees", "fieldtype": "Int", "width": 150}
	]

	labels = [d["designation"] for d in data]
	values = [d["total_employees"] for d in data]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Total Employees",
					"values": values
				}
			]
		},
		"type": "donut"
	}

	return columns, data, None, chart
