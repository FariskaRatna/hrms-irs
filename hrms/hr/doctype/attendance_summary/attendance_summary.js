// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance Summary", {
	generate_recap: function(frm) {
        frappe.call({
            method: "hrms.hr.doctype.attendance_summary.attendance_summary.generate_recap",
            args: {
                docname: frm.doc.name
            },
            callback: function(r) {
                if(!r.exc) {
                    frm.reload_doc();
                }
            }
        });
    }
});


