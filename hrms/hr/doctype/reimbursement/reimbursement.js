// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Reimbursement", {
	employee(frm) {
        if (!frm.doc.employee) return;

        frappe.db.get_value("Employee", frm.doc.employee, ["hrd_user"])
            .then(r => {
                frm.set_value("hrd_user", r.message.hrd_user);
            });
	},
});
