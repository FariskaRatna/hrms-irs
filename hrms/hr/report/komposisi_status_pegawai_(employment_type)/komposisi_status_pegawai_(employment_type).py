# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql(f"""
		SELECT
			employment_type,
			COUNT(name) AS total_employees
		FROM `tabEmployee`
		WHERE status = 'Active'
		GROUP BY employment_type
		ORDER BY employment_type
	""", as_dict=True)

	columns = [
		{"label": "Employment Type", "fieldname": "employment_type", "fieldtype": "Data", "width": 180},
		{"label": "Total Employees", "fieldname": "total_employees", "fieldtype": "Int", "width": 150}
	]

	labels = [d["employment_type"] for d in data]
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
		"type": "pie"
	}


	return columns, data, None, chart
