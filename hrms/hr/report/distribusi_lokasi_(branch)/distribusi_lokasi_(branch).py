# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql(f"""
		SELECT
			branch,
			COUNT(name) AS total_employees
		FROM `tabEmployee`
		WHERE status = 'Active'
		GROUP BY branch
		ORDER BY branch
	""", as_dict=True)

	columns = [
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Data", "width": 180},
		{"label": "Total Employees", "fieldname": "total_employees", "fieldtype": "Int", "width": 150}
	]

	labels = [d["branch"] for d in data]
	values = [d["total_employees"] for d in data]

	chart = {
		"data" : {
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


