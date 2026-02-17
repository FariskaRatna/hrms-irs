# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import calendar

def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql(f"""
		select
			year(a.attendance_date) as year,
			month(a.attendance_date) as month,
			count(*) as absent_days
		from `tabAttendance` a
		where a.status = 'Absent'
		group by year, month
		order by year, month
	""", as_dict=True)

	result = []

	for d in data:
		days_in_month = calendar.monthrange(d.year, d.month)[1]
		working_days = days_in_month * 0.7
		total_employees = frappe.db.count("Employee", {"status": "Active"})
		total_workdays = total_employees * working_days

		absent_rate = round((d.absent_days / total_workdays) * 100, 2)

		result.append({
			"period": f"{d.year}-{str(d.month).zfill(2)}",
			"absent_days": d.absent_days,
			"absenteeism_rate": absent_rate
		})


	columns = [
		{"label": "Period", "fieldname": "period", "fieldtype": "Data", "width": 120},
		{"label": "Absent Days", "fieldname": "absent_days", "fieldtype": "Int", "width": 140},
		{"label": "Absenteeism Rate (%)", "fieldname": "absenteeism_rate", "fieldtype": "Float", "width": 160},
	]

	labels = [r["period"] for r in result]
	rates = [r["absenteeism_rate"] for r in result]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Absenteeism Rate (%)",
					"values": rates
				}
			]
		},
		"type": "line"
	}

	return columns, data, None, chart
