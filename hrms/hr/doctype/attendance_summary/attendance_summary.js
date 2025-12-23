// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance Summary", {
    refresh(frm) {
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


