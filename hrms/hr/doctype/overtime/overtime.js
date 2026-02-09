// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime", {
    setup: function (frm) {
        frm.set_query("pm_user", function () {
            return {
                query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
                filters: {
                    employee: frm.doc.employee,
                    doctype: frm.doc.doctype
                },  
            };
        });
        frm.set_query("employee", erpnext.queries.employee);

        frm.trigger("toggle_employee_read_only")
    },

    employee(frm) {
        frm.trigger("set_pm_user");
    },

    assigned_by: function (frm) {
        frm.trigger("toggle_approval_editable")
        if (frm.doc.assigned_by) {
            frappe.db.get_value(
                "User",
                frm.doc.assigned_by,
                "full_name"
            ).then(r => {
                if (r && r.message && r.message.full_name) {
                    frm.set_value("assigned_by_name", r.message.full_name);
                }
            });
        }
    },

    onload(frm) {
        frm.trigger("render_attachment_preview");
    },

    refresh(frm) {
        frm.trigger("toggle_employee_read_only")
        frm.trigger("toggle_approval_editable")

        if (!frm.is_new() && frm.doc.docstatus === 0 && frm.perm[0].submit == 1) {

            frm.page.set_primary_action(__("Submit"), function () {
                frappe.confirm(
                    __("Permanently submit Overtime for {0}?", [frm.doc.employee_name || frm.doc.employee]),
                    function () {
                        frappe.call({
                            method: "frappe.client.submit",
                            args: { doc: frm.doc },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message: __("Overtime submitted"), indicator: "green" });
                                    frm.reload_doc();
                                }
                            }
                        });
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

        // frm.trigger("set_employee");
        // frm.trigger("render_attachment_preview");
        // frm.trigger("sync_photo_preview");
        frm.trigger("set_employee");
    
        // Panggil dengan delay bertingkat
        setTimeout(() => {
            frm.trigger("render_attachment_preview");
            frm.trigger("sync_photo_preview");
        }, 100);
        
        setTimeout(() => {
            frm.trigger("render_attachment_preview");
        }, 300);
    },

    after_save(frm) {
        frm.trigger("render_attachment_preview");
    },

    photo(frm) {
        frm.trigger("render_attachment_preview");
        frm.trigger("sync_photo_preview");
    },

    validate(frm) {
        if (!frm.doc.assigned_by || !frm.doc.employee) return;

        if (frm.doc.assigned_by === frm.doc.owner) {
            frappe.msgprint({
                title: __("Invalid Assignment"),
                message: __("You cannot assign overtime to yourself."),
                indicator: "red"
            });
            frappe.validated = false;
        }
    },

    async set_employee(frm) {
        if (frm.doc.employee) return;

        const employee = await hrms.get_current_employee(frm);
        if (employee) {
            frm.set_value("employee", employee);
        }
    },

    set_pm_user: function (frm) {
        if (frm.doc.employee) {
            return frappe.call({
                method: "hrms.hr.doctype.overtime.overtime.get_pm_user",
                args: {
                    employee: frm.doc.employee,
                },
                callback: function (r) {
                    if (r && r.message) {
                        frm.set_value("pm_user", r.message);
                    }
                },
            });
        }
    },

    toggle_employee_read_only: function(frm) {
        const allowed_roles = ["System Manager", "HR Manager", "HR User", "Project Manager"];

        const has_access = allowed_roles.some(role =>
            frappe.user.has_role(role)
        );

        frm.set_df_property("employee", "read_only", !has_access);
    },

    toggle_approval_editable: function(frm) {
        const user = frappe.session.user;
        const is_assigned_by = frm.doc.assigned_by && frm.doc.assigned_by === user;
        const allowed_user = ["System Manager", "HR Manager", "HR User", "Project Manager"];

        const override = allowed_user.some(role => frappe.user.has_role(role));

        frm.set_df_property("approval_status", "read_only", !(is_assigned_by || override));
    },

    // render_attachment_preview: function(frm) {
    //     setTimeout(() => {
    //         const url = frm.doc.photo;
    //         const field = frm.fields_dict.photo;
    //         if (!field) return;

    //         const $a = $(field.$wrapper).find("a.attached-file-link");
    //         if (!url || !$a.length) return;

    //         const filename = url.split("/").pop();
    //         $a.text(filename);
    //         $a.attr("title", filename);
    //     }, 50);
    // },

    render_attachment_preview: function(frm) {
        const url = frm.doc.photo;
        const field = frm.fields_dict.photo;
        if (!field) return;

        if (frm._photo_render_interval) {
            clearInterval(frm._photo_render_interval);
        }

        const forceRender = () => {
            const $wrapper = $(field.$wrapper);
            const $controlValue = $wrapper.find('.control-value');
            
            if (!$controlValue.length) return;

            $controlValue.empty();
            
            if (!url) {
                if (frm.doc.docstatus !== 1) {
                    $controlValue.html(`
                        <div class="control-input" style="display: block;">
                            <div class="file-upload-area padding"></div>
                        </div>
                    `);
                    field.df.options = field.df.options || {};
                    field.refresh();
                }
                return;
            }
            
            const filename = url.split("/").pop();
            
            let html = '';
            
            if (frm.doc.docstatus !== 1) {
                html += `
                    <div class="attached-file" style="margin-bottom: 8px;">
                        <div class="ellipsis">
                            <i class="fa fa-paperclip"></i>
                            <a href="${url}" target="_blank" class="attached-file-link">${filename}</a>
                        </div>
                        <div class="btn-group pull-right">
                            <a class="btn btn-xs btn-default remove-attach-btn" data-file-url="${url}">
                                <i class="fa fa-times"></i>
                            </a>
                        </div>
                    </div>
                    <div class="clearfix"></div>
                    <div class="control-input" style="display: block;">
                        <div class="file-upload-area padding" style="margin-top: 10px;"></div>
                    </div>
                `;
            } else {
                html += `
                    <div class="attached-file">
                        <div class="ellipsis">
                            <i class="fa fa-paperclip"></i>
                            <a href="${url}" target="_blank" class="attached-file-link">${filename}</a>
                        </div>
                    </div>
                `;
            }
            
            $controlValue.html(html);
            
            $controlValue.find('.remove-attach-btn').on('click', function(e) {
                e.preventDefault();
                frm.set_value('photo', '');
            });
            
            if (frm.doc.docstatus !== 1) {
                const $uploadArea = $controlValue.find('.file-upload-area');
                if ($uploadArea.length) {
                    field.setup_attach();
                }
            }
        };

        frm._photo_render_interval = setInterval(forceRender, 200);
        
        setTimeout(forceRender, 0);
        setTimeout(forceRender, 100);
        setTimeout(forceRender, 300);
    },


    sync_photo_preview: function(frm) {
        const url = frm.doc.photo;
		const w = frm.fields_dict.photo_preview?.$wrapper;
		if (!w) return;

		if (!url) {
			w.html("");
			return;
		}

		w.html(`
		<div style="margin-top:10px">
			<img src="${encodeURI(url)}"
				style="max-width:240px; max-height:240px; width:auto; height:auto;
						object-fit:contain; border-radius:10px; border:1px solid #ddd;" />
		</div>
		`);
    },

});

