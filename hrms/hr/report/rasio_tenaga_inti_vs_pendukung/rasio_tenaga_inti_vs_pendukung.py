# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	core = frappe.db.sql(f"""
		select
			department as core_department,
			count(name) as total_core
		from `tabEmployee`
		where status = 'Active' and department in ('Information System 1', 'Information System 2', 'Information System 3', 'Data Management')
		group by department
		order by department
	""", as_dict=True)

	support = frappe.db.sql(f"""
		select
			department as support_department,
			count(name) as total_support
		from `tabEmployee`
		where status = 'Active' and department in ('Human Resource and General Affair', 'Finance and Tax')
		group by department
		order by department
	""", as_dict=True)


	total_core = core[0]["total_core"] if core else 0
	total_support = support[0]["total_support"] if support else 0

	columns = [
		{"label": "Team", "fieldname": "team", "fieldtype": "Data", 'width': 200},
		{"label": "Total Employees", "fieldname": "total", "fieldtype": "Int", "width": 120},

	]

	data = [
		{"team": "Core Team", "total": total_core},
		{"team": "Support Team", "total": total_support},
	]

	chart = {
		"data": {
			"labels": ["Core Team", "Support Team"],
			"datasets": [
				{
					"name": "Employees",
					"values": [total_core, total_support]
				}
			]
		},
		"type": "donut"
	}
	
	return columns, data, None, chart
