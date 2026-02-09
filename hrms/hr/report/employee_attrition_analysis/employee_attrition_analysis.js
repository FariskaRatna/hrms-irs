// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Attrition Analysis"] = {
	"filters": [
		{
			fieldname: "group_by",
			label: "Group By",
			fieldtype: "Select",
			options: [
			"Department",
			"Designation",
			"Masa Kerja"
			],
			default: "Department",
			reqd: 1
		},
		// {
		// 	fieldname: "department",
		// 	label: "Department",
		// 	fieldtype: "Link",
		// 	options: "Department",
		// 	reqd: 0
		// },
		// {
		// 	fieldname: "designation",
		// 	label: "Designation",
		// 	fieldtype: "Link",
		// 	options: "Designation",
		// 	reqd: 0
		// },
	]
};
