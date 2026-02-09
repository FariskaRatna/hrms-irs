# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}

	year = filters.get("year")
	department = filters.get("department")
	metric = filters.get("metric", "total_hours")

	conditions = []
	values = {}

	if year:
		conditions.append("YEAR(from_date) = %(year)s")
		values["year"] = year
	if department:
		conditions.append("department = %(department)s")
		values["department"] = department

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "WHERE " + where_clause

	if metric == "total_hours":
		query = f"""
			SELECT
				DATE_FORMAT(from_date, '%%Y-%%m') AS month,
				SUM(total_hours) AS total_hours
			FROM `tabOvertime Slip`
			{where_clause}
			GROUP BY DATE_FORMAT(from_date, '%%Y-%%m')
			ORDER BY DATE_FORMAT(from_date, '%%Y-%%m')
		"""

		data = frappe.db.sql(query, values, as_dict=True)

		columns = [
			{"label": "Month", "fieldname": "month", "fieldtype": "Data"},
			{"label": "Total Overtime Hours", "fieldname": "total_hours", "fieldtype": "Float"}
		]

		chart = {
			"data": {
				"labels": [d.month for d in data],
				"datasets": [
					{"name": "Total Overtime Hours", "values": [d.total_hours for d in data]}
				]
			},
			"type": "line"
		}
	
	elif metric == "avg_by_dept":
		query = f"""
			SELECT
				DATE_FORMAT(from_date, '%%Y-%%m') AS month,
				department,
				AVG(total_hours) AS avg_hours
			FROM `tabOvertime Slip`
			{where_clause}
			GROUP BY DATE_FORMAT(from_date, '%%Y-%%m'), department
			ORDER BY DATE_FORMAT(from_date, '%%Y-%%m'), department
		"""

		data = frappe.db.sql(query, values, as_dict=True)

		columns = [
			{"label": "Month", "fieldname": "month", "fieldtype": "Data"},
			{"label": "Department", "fieldname": "department", "fieldtype": "Data"},
			{"label": "Avg Overtime Hours", "fieldname": "avg_hours", "fieldtype": "Float"}
		]

		labels = sorted(list({d.month for d in data}))
		departments = sorted(list({d.department for d in data}))

		dataset_map = {dept: [] for dept in departments}

		for month in labels:
			for dept in departments:
				row = next((d for d in data if d.month == month and d.department == dept), None)
				dataset_map[dept].append(row.avg_hours if row else 0)


		chart = {
			"data": {
				"labels": list({d.month for d in data}),
				"datasets": [
					{
						"name": dept,
						"values": dataset_map[dept]
					} for dept in departments
				]
			},
			"type": "bar"
		}
	
	elif metric == "employee_count":
		query = f"""
			SELECT
				DATE_FORMAT(from_date, '%%Y-%%m') AS month,
				COUNT(DISTINCT employee) AS employee_count
			FROM `tabOvertime Slip`
			{where_clause}
			GROUP BY DATE_FORMAT(from_date, '%%Y-%%m')
			ORDER BY DATE_FORMAT(from_date, '%%Y-%%m')
		"""
		data = frappe.db.sql(query, values, as_dict=True)

		columns = [
			{"label": "Month", "fieldname": "month", "fieldtype": "Data"},
			{"label": "Employee with Overtime", "fieldname": "employee_count", "fieldtype": "Int"}
		]

		chart = {
			"data": {
				"labels": [d.month for d in data],
				"datasets": [
					{"name": "Employee with Overtime", "values": [d.employee_count for d in data]}
				]
			},
			"type": "bar"
		}
	
	else:
		query = f"""
			SELECT
				employee,
				employee_name,
				SUM(total_hours) AS total_hours
			FROM `tabOvertime Slip`
			{where_clause}
			GROUP BY employee, employee_name
			ORDER BY total_hours DESC
			LIMIT 5
		"""

		data = frappe.db.sql(query, values, as_dict=True)

		columns = [
			{"label": "Employee", "fieldname": "employee_name", "fieldtype": "Data"},
			{"label": "Total Overtime Hours", "fieldname": "total_hours", "fieldtype": "Float"}
		]

		chart = {
			"data": {
				"labels": [d.month for d in data],
				"datasets": [
					{"name": "Top 5 Overtime", "values": [d.total_hours for d in data]}
				]
			},
			"type": "bar"
		}

	return columns, data, None, chart
