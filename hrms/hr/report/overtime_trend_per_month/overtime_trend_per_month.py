# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	filters = filters or {}

	conditions = []
	values = {}

	if filters.get("employee"):
		conditions.append("employee = %(employee)s")
		values["employee"] = filters["employee"]

	if filters.get("department"):
		conditions.append("department = %(department)s")
		values["department"] = filters["department"]

	where_clause = (
		"WHERE " + " AND ".join(conditions)
		if conditions else ""
	)

	data = frappe.db.sql(f"""
		SELECT
			DATE_FORMAT(from_date, '%%Y-%%m') AS month,
			SUM(total_hours) AS total_hours
		FROM `tabOvertime Slip`
		{where_clause}
		GROUP BY DATE_FORMAT(from_date, '%%Y-%%m')
		ORDER BY DATE_FORMAT(from_date, '%%Y-%%m')
	""", values=values, as_dict=True)

	result = []

	for d in data:
		total_hours = d.total_hours or 0  
		result.append({
			"month": d.month,
			"total_hours": round(total_hours, 2)
		})

	columns = [
		{
			"label": "Month",
			"fieldname": "month",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Total Overtime Hours",
			"fieldname": "total_hours",
			"fieldtype": "Float",
			"width": 180
		},
	]

	labels = [r["month"] for r in result]
	hours = [r["total_hours"] for r in result]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Overtime Hours",
					"values": hours
				}
			]
		},
		"type": "line"
	}

	return columns, result, None, chart

