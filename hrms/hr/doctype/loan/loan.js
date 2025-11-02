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
	}
});
