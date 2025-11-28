// Untuk tampilan status pada leave application, tidak digunakan karena yang digunakan yang approval status

// frappe.listview_settings["Leave Application"] = {
// 	add_fields: [
// 		"leave_type",
// 		"employee",
// 		"employee_name",
// 		"total_leave_days",
// 		"from_date",
// 		"to_date",
// 	],
// 	has_indicator_for_draft: 1,
// 	get_indicator: function (doc) {
// 		const status_color = {
// 			// Approved: "green",
// 			// Rejected: "red",
// 			// Open: "orange",
// 			Draft: "red",
// 			Cancelled: "red",
// 			Submitted: "blue",
// 		};
// 		const status =
// 			!doc.docstatus && ["Approved", "Rejected"].includes(doc.approval_status) ? "Draft" : doc.approval_status;
// 		return [__(status), status_color[status], "status,=," + doc.approval_status];
// 	},
// };
