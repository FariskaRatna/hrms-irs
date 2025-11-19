// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Attendance", {
	refresh(frm) {
		if (frm.doc.__islocal && !frm.doc.attendance_date) {
			frm.set_value("attendance_date", frappe.datetime.get_today());
		}

		frm.set_query("employee", () => {
			return {
				query: "erpnext.controllers.queries.employee_query",
			};
		});

		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.page.set_primary_action(__("Submit"), function () {
				frappe.confirm(
					`Permanently submit Attendance ${frm.doc.name} for ${frm.doc.employee_name || frm.doc.employee}?`,
					function () {
						frappe.call({
							method: "frappe.client.submit",
							args: {
								doc: frm.doc
							},
							callback: function (r) {
								if (!r.exc) {
									frappe.show_alert({ message: __("Attendance submitted"), indicator: "green" });
									frm.reload_doc();
								}
							}
						});
					},
					function () {
						frappe.show_alert({ message: __("Attendance cancelled"), indicator: "red" });
					}
				);
			});
		}
	},
});
