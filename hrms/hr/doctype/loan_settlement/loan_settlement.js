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
                    __("Permanently submit Loan Settlement for {0}?", [frm.doc.employee_name || frm.doc.employee]),
    
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

    transaction_proof(frm) {
        frm.trigger("attachment_filename");
    },

    attachment_filename: function(frm) {
        const url = frm.doc.transaction_proof;
		const field = frm.fields_dict.transaction_proof;
		if (!field) return;

		const $attach = $(field.$wrapper).find("a.attached-file-link");
		if (!url || $attach.lenth) return;

		const filename = url.split("/").pop();
		$attach.text(filename);
		$attach.attr("title", filename);
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

