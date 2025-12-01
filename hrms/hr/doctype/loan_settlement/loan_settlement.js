// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loan Settlement", {
    refresh: function(frm) {
        // Kalau employee sudah ada, panggil fungsi set filter
        if (frm.doc.employee) {
            set_loan_filter(frm);
        }

        if (!frm.is_new() && frm.doc.docstatus === 0 && frm.perm[0].submit == 1) {
            frm.page.set_primary_action(__("Submit"), function () {
                frappe.confirm(
                    `Permanently submit Loan Settlement for ${frm.doc.employee_name || frm.doc.employee}?`,
                    function () {
                        frappe.call({
                            method: "frappe.client.submit",
                            args: {
                                doc: frm.doc
                            },
                            callback (r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message: __("Loan Settlement submitted"), indicator: "green" });
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function () {
                        frappe.show_alert({ message: __("Loan Settlement cancelled"), indicator: "red" });
                    }
                );
            });
        }
    },

    employee: function(frm) {
        // Kalau employee diubah, update filter loan juga
        if (frm.doc.employee) {
            set_loan_filter(frm);
        } else {
            frm.set_query('loan', () => {
                return { filters: { name: "" } };
            });
        }

        if (!frm.doc.employee) return;

        frappe.db.get_value("Employee", frm.doc.employee, ["user_id"])
            .then(r => {
                frm.set_value("hrd_user", r.message.user_id);
            });
    }
});

function set_loan_filter(frm) {
    frm.set_query('loan', function() {
        return {
            filters: {
                employee: frm.doc.employee,
                repayment_status: "Unpaid",
                status: "Active"
            }
        };
    });
}

