// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Overtime Trend"] = {
	"filters": [
		{
			fieldname: "year",
			label: "Year",
			fieldtype: "Int",
			default: new Date().getFullYear()
		},
		{
			fieldname: "department",
			label: "Department",
			fieldtype: "Link",
			options: "Department"
		},
		{
			fieldname: "metric",
			label: "Metric",
			fieldtype: "Select",
			options: [
				{ label: "Total OT Hours per Month", value: "total_hours" },
				{ label: "Average OT by Dept / Month", value: "avg_by_dept" },
				{ label: "Employees with OT per Month", value: "employee_count" },
				{ label: "Top 5 Employee OT", value: "top_employee" }
			],
			default: "total_hours"
		}
	]
};
