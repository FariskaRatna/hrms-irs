# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql(f"""
		SELECT
			division,
			employment_type,
			COUNT(name) AS total_employees
		FROM `tabEmployee`
		WHERE status = 'Active'
		GROUP BY division, employment_type
		ORDER BY division, employment_type
	""", as_dict=True)

	columns = [
		{"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 180},
		{"label": "Employment Type", "fieldname": "employment_type", "fieldtype": "Data", "width": 180},
		{"label": "Total Employees", "fieldname": "total_employees", "fieldtype": "Int", "width": 150}
	]

	department = sorted(list({d["division"] for d in data}))
	emp_types = sorted(list({d["employment_type"] for d in data}))

	datasets = []
	for et in emp_types:
		datasets.append({
			"name": et,
			"values": [
				next(
					(d["total_employees"] for d in data if d["division"] == div and d["employment_type"] == et),
					0
				)
				for div in department
			]
		})

	chart = {
		"data": {
			"labels": department,
			"datasets": datasets
		},
		"type": "bar",
		"barOptions": {
			"stacked": True
		}
	}
	return columns, data
