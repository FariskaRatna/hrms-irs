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

    refresh(frm) {
        frm.trigger("toggle_employee_read_only")

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
    },

    validate(frm) {
        if (!frm.doc.assigned_by || !frm.doc.employee) return;

        const current_user = frappe.session.user;

        if (frm.doc.assigned_by === current_user) {
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
    }

});

