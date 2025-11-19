// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Slip", {
	refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.page.set_primaru_action(__("Submit"), function () {
                frappe.confirm(
                    `Permanently submit Overtime Slip ${frm.doc.name} for ${frm.doc.employee_name || frm.doc.employee}?`,
                    function () {
                        frappe.call({
                            method: "frappe.client.submit",
                            args: {
                                doc: frm.doc
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message: __("Overtime Slip submitted"), indicator: "green" });
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function () {
                        frappe.show_alert({ message: __("Overtime Slip cancelled"), indicator: "red" });
                    }
                );
            });
        }
	},
});
