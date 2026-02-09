# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	
	employee = filters.get("employee")
	department = filters.get("department")

	conditions = []
	values = {}

	if employee:
		conditions.append("employee = %(employee)s")
		values["employee"] = employee
	if department:
		conditions.append("department = %(department)s")
		values["department"] = department
	
	condition_sql = " AND ".join(conditions) if conditions else "1=1"

	data = frappe.db.sql(f"""
		SELECT
			leave_category,
			COUNT(name) AS total_applications
		FROM `tabLeave Application`
		WHERE {condition_sql}
		GROUP BY leave_category
		ORDER BY total_applications DESC
	""", values, as_dict=True)

	columns = [
		{"label": "Leave Category", "fieldname": "leave_category", "fieldtype": "Data", "width": 200},
		{"label": "Total Applications", "fieldname": "total_applications", "fieldtype": "Int", "width": 150},
	]

	chart = {
		"data": {
			"labels": [d["leave_category"] for d in data],
			"datasets": [{
				"name": "Total Applications",
				"values": [d["total_applications"] for d in data],
			}]
		},
		"type": "bar"
	}

	return columns, data, None, chart
