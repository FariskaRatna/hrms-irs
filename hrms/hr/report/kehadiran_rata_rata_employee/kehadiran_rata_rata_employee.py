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
			COUNT(*) AS present_days
		FROM `tabAttendance`
		WHERE status = 'Present'
		GROUP BY year, month
		ORDER BY year, month
	""", as_dict=True)

	result = []

	for d in data:
		days_in_month = calendar.monthrange(d.year, d.month)[1]
		working_days = days_in_month * 0.7

		total_employees = frappe.db.count("Employee", {"status": "Active"})
		total_workdays = total_employees * working_days

		present_days = d.present_days or 0 

		attendance_rate = round((present_days / total_workdays) * 100, 2) if total_workdays else 0

		result.append({
			"period": f"{d.year}-{str(d.month).zfill(2)}",
			"present_days": present_days,
			"attendance_rate": attendance_rate
		})

	columns = [
		{"label": "Period", "fieldname": "period", "fieldtype": "Data", "width": 120},
		{"label": "Present Days", "fieldname": "present_days", "fieldtype": "Int", "width": 140},
		{"label": "Attendance Rate (%)", "fieldname": "attendance_rate", "fieldtype": "Float", "width": 170},
	]

	labels = [r["period"] for r in result]
	rates = [r["attendance_rate"] for r in result]

	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Attendance Rate (%)",
					"values": rates
				}
			]
		},
		"type": "line"
	}

	return columns, result, None, chart