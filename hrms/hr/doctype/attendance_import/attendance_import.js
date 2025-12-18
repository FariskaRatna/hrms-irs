// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Attendance Import", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Attendance Import', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button('Process File', () => {
                frappe.call({
                    method: 'hrms.hr.doctype.attendance_import.attendance_import.process_file', 
                    args: { docname: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Processing attendance file, please wait...'),
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__('File processed successfully!'));
                        }
                    }
                });
            });
        }
    }
});


