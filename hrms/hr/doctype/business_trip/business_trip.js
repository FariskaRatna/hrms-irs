// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Trip", {
	employee(frm) {
        if (!frm.doc.employee) return;

        frappe.db.get_value("Employee", frm.doc.employee, ["project_manager", "hrd_user"])
            .then(r => {
                const pm = r.message.project_manager;
                const hrd = r.message.hrd_user;

                if (pm) {
                    frappe.db.get_value("Employee", pm, "user_id")
                        .then(u => frm.set_value("pm_user", u.message.user_id));
                }

                if (hrd) {
                    frappe.db.get_value("Employee", hrd, "user_id")
                        .then(u => frm.set_value("hrd_user", u.message.user_id));
                }
            });
	},
    
    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0 && frm.perm[0].submit == 1) {
            frm.page.set_primary_action(__("Submit"), function () {
                frappe.confirm(
                    `Permanently submit Business Trip ${frm.doc.employee_name || frm.doc.employee}?`,
                    function () {
                        frappe.call({
                            method: "frappe.client.submit",
                            args: {
                                doc: frm.doc
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message:__("Business Trip submitted"), indicator: "green"});
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function () {
                        frappe.show_alert({ message: __("Submission cancelled"), indicator: "red" });
                    }
                );
            });
        }
    }
});
