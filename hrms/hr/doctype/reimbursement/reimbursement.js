// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Reimbursement", {
	employee(frm) {
        if (!frm.doc.employee) return;

        frappe.db.get_value("Employee", frm.doc.employee, ["hrd_user", "balance"])
            .then(r => {
                frm.set_value("hrd_user", r.message.hrd_user);
                frm.set_value("balance", r.message.balance);
            });
	},

    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0 && frm.perm[0] == 1) {
            frm.page.set_primary_action(__("Submit"), function() {
                frappe.confirm(
                    __("Permanently submit Reimbursement for {0}?", [frm.doc.employee_name || frm.doc.employee]),
                    function () {
                        frappe.call({
                            method: "frappe.client.submit",
                            args: {
                                doc: frm.doc
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message: __("Reimbursement submitted"), indicator: "green" });
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

        frm.trigger("attachment_filename");
    },

    document_photo(frm) {
        frm.trigger("attachment_filename");
    },

    attachment_filename: function(frm) {
        const url = frm.doc.document_photo;
		const field = frm.fields_dict.document_photo;
		if (!field) return;

		const $attach = $(field.$wrapper).find("a.attached-file-link");
		if (!url || $attach.lenth) return;

		const filename = url.split("/").pop();
		$attach.text(filename);
		$attach.attr("title", filename);
    }
});
