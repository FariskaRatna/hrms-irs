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

    refresh(frm) {
        frm.trigger("toggle_employee_read_only")
        frm.trigger("toggle_approval_editable")

        if (!frm.is_new() && frm.doc.docstatus === 0 && frm.perm[0].submit == 1) {

            frm.page.set_primary_action(__("Submit"), function () {
                frappe.confirm(
                    `Permanently submit Overtime for ${frm.doc.employee_name || frm.doc.employee}?`,
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

        frm.trigger("set_employee");
        frm.trigger("render_attachment_preview");
        frm.trigger("sync_photo_preview");
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

    render_attachment_preview: function(frm) {
        const url = frm.doc.photo;
        const field = frm.fields_dict.photo;
        if (!field) return;

        const $a = $(field.$wrapper).find("a.attached-file-link");
        if (!url || !$a.length) return;

        const filename = url.split("/").pop();
        $a.text(filename);    
        $a.attr("title", filename);
    },

    sync_photo_preview: function(frm) {
        const file_url = frm.doc.photo

        if (!file_url) {
            frm.set_value("image", "");
            frm.toggle_display("image", false);
            return
        }

        frm.set_value("image", file_url);
        frm.toggle_display("image", true);
    },

});

