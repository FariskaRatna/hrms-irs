# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from collections import defaultdict

def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql("""
		SELECT
			DATE_FORMAT(from_date, '%Y-%m') AS month,
			department,
			SUM(total_hours) AS total_hours
		FROM `tabOvertime Slip`
		WHERE department IS NOT NULL
		GROUP BY
			DATE_FORMAT(from_date, '%Y-%m'),
			department
		ORDER BY
			DATE_FORMAT(from_date, '%Y-%m'),
			department
	""", as_dict=True)

	months = sorted({d.month for d in data})
	departments = sorted({d.department for d in data})

	matrix = defaultdict(lambda: defaultdict(float))
	for d in data:
		matrix[d.month][d.department] = d.total_hours or 0

	result = []
	for m in months:
		row = {"month": m}
		for dept in departments:
			row[dept] = round(matrix[m].get(dept, 0), 2)
		result.append(row)

	columns = [{
		"label": "Month",
		"fieldname": "month",
		"fieldtype": "Data",
		"width": 120
	}]

	for dept in departments:
		columns.append({
			"label": dept,
			"fieldname": dept,
			"fieldtype": "Float",
			"width": 140
		})

	datasets = []
	for dept in departments:
		datasets.append({
			"name": dept,
			"values": [round(matrix[m].get(dept, 0), 2) for m in months]
		})

	chart = {
		"data": {
			"labels": months,
			"datasets": datasets
		},
		"type": "bar",
	}

	return columns, result, None, chart

