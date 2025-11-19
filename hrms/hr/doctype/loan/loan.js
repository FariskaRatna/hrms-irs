// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loan", {
	refresh(frm) {
        if (frm.doc.repayment_tracking && frm.doc.repayment_tracking.length > 0) {
            frm.add_custom_button("Download Repayment Report", function() {
                frappe.call({
                    method: "hrms.hr.doctype.loan.loan.download_repayment_excel",
                    args: { loan_name: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            window.open(r.message);
                        }
                    }
                });
            }, __("Tools"));
        }

        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.page.set_primary_action(__("Submit"), function () {
                frappe.confirm(
                    `Permanently submit Loan Summary ${frm.doc.name} for ${frm.doc.employee_name || frm.doc.employee}?`,
                    function() {
                        frappe.call({
                            method: "frappe.client.submit",
                            args: {
                                doc: frm.doc
                            },
                            callback (r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message: __("Loan Summary submitted"), indicator: "green" });
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function () {
                        frappe.show_alert({ message: __("Loan Summary cancelled"), indicator: "red" });
                    }
                );
            });
        }
	}
});
