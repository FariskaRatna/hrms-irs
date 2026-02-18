# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql(f"""
		SELECT
			department,
			employment_type,
			COUNT(name) AS total_employees
		FROM `tabEmployee`
		WHERE status = 'Active'
			AND department IS NOT NULL
			AND employment_type IS NOT NULL
		GROUP BY department, employment_type
		ORDER BY department, employment_type
	""", as_dict=True)

	columns = [
		{"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 180},
		{"label": "Employment Type", "fieldname": "employment_type", "fieldtype": "Data", "width": 180},
		{"label": "Total Employees", "fieldname": "total_employees", "fieldtype": "Int", "width": 150}
	]

	department = sorted(list({d["department"] for d in data}))
	emp_types = sorted(list({d["employment_type"] for d in data}))

	datasets = []
	for et in emp_types:
		datasets.append({
			"name": et,
			"values": [
				next(
					(d["total_employees"] for d in data if d["department"] == div and d["employment_type"] == et),
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
		"colors": ["#F26076", "#4194f3", "#84ebf8", "#48bb74"], 
		"barOptions": {
			"stacked": 1,
			"spaceRatio": 0.5
		},
		"height": 280,
		"axisOptions": {
			"xAxisMode": "tick",
			"xIsSeries": 0
		}
	}
	return columns, data, None, chart
