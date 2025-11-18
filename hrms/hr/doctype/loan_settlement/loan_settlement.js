// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loan Settlement", {
    refresh: function(frm) {
        // Kalau employee sudah ada, panggil fungsi set filter
        if (frm.doc.employee) {
            set_loan_filter(frm);
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

        frappe.db.get_value("Employee", frm.doc.employee, ["hrd_user"])
            .then(r => {
                frm.set_value("hrd_user", r.message.hrd_user);
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

