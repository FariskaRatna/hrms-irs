frappe.ui.form.on("Reimbursement", {
    employee(frm) {
        if (!frm.doc.employee) return;

        frappe.db.get_value("Employee", frm.doc.employee, ["hrd_user", "balance"])
            .then(r => {
                frm.set_value("hrd_user", r.message.hrd_user);
                frm.set_value("balance", r.message.balance);
            });
    },

    onload(frm) {
        frm.trigger("attachment_filename");
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

        setTimeout(() => {
            frm.trigger("attachment_filename");
        }, 100);
        
        setTimeout(() => {
            frm.trigger("attachment_filename");
        }, 300);
    },

    after_save(frm) {
        frm.trigger("attachment_filename");
    },

    document_photo(frm) {
        frm.trigger("attachment_filename");
    },

    attachment_filename: function(frm) {
        const url = frm.doc.document_photo;
        const field = frm.fields_dict.document_photo;
        if (!field) return;

        if (frm._photo_render_interval) {
            clearInterval(frm._photo_render_interval);
        }

        const forceRender = () => {
            const $wrapper = $(field.$wrapper);
            const $controlValue = $wrapper.find('.control-value');
            
            if (!$controlValue.length) return;

            // TAMBAHAN: Replace text link yang masih ada path (sebelum submit)
            if (url) {
                const filename = url.split("/").pop();
                
                $wrapper.find('a').each(function() {
                    const $link = $(this);
                    const text = $link.text().trim();
                    
                    // Jika text masih mengandung path, replace dengan filename
                    if (text.includes('/') || text.includes('private') || text.includes('files')) {
                        $link.text(filename);
                        $link.attr('title', filename);
                    }
                });
            }

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
                frm.set_value('document_photo', '');
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
    }
});