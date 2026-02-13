# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql(f"""
		select
			designation,
			sum(case when status = 'Left' then 1 else 0 end) as attrition,
			sum(case when status = 'Active' then 1 else 0 end) as active
		from `tabEmployee`
		group by designation
		order by designation	
	""", as_dict=True)

	columns = [
		{"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 180},
		{"label": "Attrition", "fieldname": "attrition", "fieldtype": "Int", "width": 150},
		{"label": "Active Employees", "fieldname": "active", "fieldtype": "Int", "width": 150}
	]

	labels = [d["designation"] for d in data]
	attrition = [d["attrition"] for d in data]
	active = [d["active"] for d in data]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "Attrition", "values": attrition},
				{"name": "Active Employees", "values": active}
			]
		},
		"type": "bar",
	}

	return columns, data, None, chart
