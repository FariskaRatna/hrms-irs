# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import date


def execute(filters=None):
	filters = filters or {}

	group_by = filters.get("group_by", "department")
	department = filters.get("department")
	designation = filters.get("designation")

	conditions = ["status = 'Left'", "date_of_joining IS NOT NULL"]
	values = {}

	if department:
		conditions.append("department = %(department)s")
		values["department"] = department
	if designation:
		conditions.append("designation = %(designation)s")
		values["designation"] = designation

	condition_sql = " AND ".join(conditions)

	employees = frappe.db.sql(f"""
		SELECT
			employee, employee_name, department, designation, date_of_joining, relieving_date
		FROM `tabEmployee`
		WHERE {condition_sql}
	""", values, as_dict=True)

	today = date.today()
	result = {}

	for emp in employees:
		end_date = emp.relieving_date or today
		months = (end_date - emp.date_of_joining).days // 30

		if months < 12:
			bucket = "< 1 Tahun"
		elif months < 36:
			bucket = "1 - 3 Tahun"
		elif months < 60:
			bucket = "3 - 5 Tahun"
		else:
			bucket = "> 5 Tahun"

		if group_by == "department":
			key = emp.department or "Unknown"
		elif group_by == "designation":
			key = emp.designation or "Unknown"
		else:
			key = bucket

	columns = [
		{
			"label": group_by.replace("_", " ").title(),
			"fieldname": "group",
			"fieldtype": "Data"
		},
		{
			"label": "Jumlah Attrition",
			"fieldname": "count",
			"fieldtype": "Int"
		}
	]

	data = [{"group": k, "count": v} for k, v in result.items()]

	chart = {
		"data": {
			"labels": [d["group"] for d in data],
			"datasets": [
				{
					"name": "Attrition",
					"values": [d["count"] for d in data]
				}
			]
		},
		"type": "bar"
	}

	return columns, data, None, chart
