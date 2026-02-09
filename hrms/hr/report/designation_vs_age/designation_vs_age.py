# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import date


def execute(filters=None):
	filters = filters or {}

	department = filters.get("department")

	conditions = ["status = 'Active'", "date_of_birth IS NOT NULL"]
	values = {}

	if department:
		conditions.append("department = %(department)s")
		values["department"] = department

	condition_sql = " AND ".join(conditions)

	employees = frappe.db.sql(f"""
		SELECT
			designation,
			date_of_birth
		FROM `tabEmployee`
		WHERE {condition_sql}
	""", values, as_dict=True)

	today = date.today()
	result = {}

	for emp in employees:
		age = today.year - emp.date_of_birth.year - (
			(today.month, today.day) < (emp.date_of_birth.month, emp.date_of_birth.day)
		)

		if age < 25:
			bucket = "< 25"
		elif age <= 30:
			bucket = "25 - 30"
		elif age <= 35:
			bucket = "31 - 35"
		elif age <= 40:
			bucket = "36 - 40"
		else:
			bucket = "> 40"

		key = (emp.designation or "Unknown", bucket)
		result[key] = result.get(key, 0) + 1

	data = []
	for (designation, bucket), count in result.items():
		data.append({
			"designation": designation,
			"age_group": bucket,
			"count": count
		})

	columns = [
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Data"},
        {"label": "Age Group", "fieldname": "age_group", "fieldtype": "Data"},
        {"label": "Total Employee", "fieldname": "count", "fieldtype": "Int"},
    ]

	labels = sorted(list({d["age_group"] for d in data}))
	designations = sorted(list({d["designation"] for d in data}))

	datasets = []
	for des in designations:
		datasets.append({
			"name": des,
			"values": [next((d["count"] for d in data if d["designation"] == des and d["age_group"] == ag), 0) for ag in labels]
		})

	chart = {
		"data": {
			"labels": labels,
			"datasets": datasets
		},
		"type": "bar"
	}
	
	
	return columns, data, None, chart
