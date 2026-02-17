# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import calendar

def execute(filters=None):
	filters = filters or {}

	data = frappe.db.sql("""
		SELECT
			YEAR(attendance_date) AS year,
			MONTH(attendance_date) AS month,
			COUNT(*) AS on_leave_days
		FROM `tabAttendance`
		WHERE status = 'On Leave'
		GROUP BY year, month
		ORDER BY year, month
	""", as_dict=True)

	result = []

	for d in data:
		days_in_month = calendar.monthrange(d.year, d.month)[1]

		working_days = days_in_month * 0.7
		total_employees = frappe.db.count("Employee", {"status": "Active"})

		total_workdays = total_employees * working_days

		on_leave_days = d.on_leave_days or 0

		leave_utilization = (
			round((on_leave_days / total_workdays) * 100, 2)
			if total_workdays else 0
		)

		result.append({
			"period": f"{d.year}-{str(d.month).zfill(2)}",
			"on_leave_days": on_leave_days,
			"leave_utilization": leave_utilization
		})

	columns = [
		{"label": "Period", "fieldname": "period", "fieldtype": "Data", "width": 120},
		{"label": "On Leave Days", "fieldname": "on_leave_days", "fieldtype": "Int", "width": 150},
		{"label": "Leave Utilization (%)", "fieldname": "leave_utilization", "fieldtype": "Float", "width": 180},
	]

	labels = [r["period"] for r in result]
	utilization = [r["leave_utilization"] for r in result]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Leave Utilization (%)",
					"values": utilization
				}
			]
		},
		"type": "line"
	}

	return columns, result, None, chart

