// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loan Application", {
	refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0 && frm.perm[0].submit == 1) {
            frm.page.set_primary_action(__("Submit"), function () {
                frappe.confirm(
                    `Permanently submit Loan Application for ${frm.doc.employee_name || frm.doc.employee}?`,
                    function () {
                        frappe.call({
                            method: "frappe.client.submit",
                            args: {
                                doc: frm.doc
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message: __("Loan Application submitted"), indicator: "green" });
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

        setTimeout(function() {
		    let save_button = frm.page.wrapper.find('.primary-action');
		    if (save_button.length > 0) {
		        save_button.hide();
		        
		        let custom_button_div = $('<div>')
		            .css({
		                'text-align': 'right',
		                'margin-top': '20px',
		                'position': 'relative',
		                'bottom': '10px',
		                'width': '100%'
		            })
		            .appendTo(frm.$wrapper.find('.form-layout'));
		            
		        save_button.appendTo(custom_button_div);
		        
		        save_button.show();
		    }
		}, 50)
	},

    employee(frm) {
        if (!frm.doc.employee) return;

        frappe.db.get_value("Employee", frm.doc.employee, ["hrd_user"])
            .then(r => {
                frm.set_value("hrd_user", r.message.hrd_user);
            });
    }
});
