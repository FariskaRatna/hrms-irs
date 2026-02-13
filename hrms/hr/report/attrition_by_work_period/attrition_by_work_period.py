# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import date

def execute(filters=None):
	filters = filters or {}

	employees = frappe.db.sql(f"""
		select
			status, date_of_joining, relieving_date
		from `tabEmployee`
	""", as_dict=True)

	today = date.today()

	buckets = {
		"< 1 Tahun": {"attrition": 0, "active": 0},
		"1 - 3 Tahun": {"attrition": 0, "active": 0},
		"3 - 5 Tahun": {"attrition": 0, "active": 0},
		"> 5 Tahun": {"attrition": 0, "active": 0},
	}

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

		if emp.status == "Left":
			buckets[bucket]["attrition"] += 1
		else:
			buckets[bucket]["active"] += 1

	data = []
	for k, v in buckets.items():
		data.append({
			"work_period": k,
			"attrition": v["attrition"],
			"active": v["active"]
		})


	columns = [
		{"label": "Work Period", "fieldname": "work_period", "fieldtype": "Data", "width": 180},
		{"label": "Attrition", "fieldname": "attrition", "fieldtype": "Int", "width": 150},
		{"label": "Active Employees", "fieldname": "active", "fieldtype": "Int", "width": 150}
	]

	labels = [d["work_period"] for d in data]
	attrition = [d["attrition"] for d in data]
	active = [d["active"] for d in data]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "Attrition", "values": attrition},
				{"name": "Active Employees", "values": active},
			]
		},
		"type": "bar"
	}


	return columns, data, None, chart