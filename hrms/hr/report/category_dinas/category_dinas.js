// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Category Dinas"] = {
	"filters": [
		{
			fieldname: "employee",
			label: "Employee",
			fieldtype: "Link",
			options: "Employee",
			reqd: 0
		},
		{
			fieldname: "department",
			label: "Department",
			fieldtype: "Link",
			options: "Department",
			reqd: 0
		}
	]
};
