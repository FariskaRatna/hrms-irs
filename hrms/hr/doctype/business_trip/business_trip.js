// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Trip", {
    setup: function (frm) {
        frm.set_query("pm_user", function () {
            return {
                query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
                filters: {
                    employee: frm.doc.employee,
                    doctype: frm.doc.doctype,
                },
            };
        });
    },

    employee(frm) {
        frm.trigger("set_pm_user");

        if (!frm.doc.employee) return;

        frappe.db.get_value("Employee", frm.doc.employee, ["hrd_user"])
        .then(r => {
            // frm.set_value("pm_user", r.message.project_manager);
            frm.set_value("hrd_user", r.message.hrd_user)
        });
    },

    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0 && frm.perm[0].submit == 1) {
            frm.page.set_primary_action(__("Submit"), function () {
                frappe.confirm(
                    `Permanently submit Business Trip ${frm.doc.employee_name || frm.doc.employee}?`,
                    function () {
                        frappe.call({
                            method: "frappe.client.submit",
                            args: {
                                doc: frm.doc
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message:__("Business Trip submitted"), indicator: "green"});
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

        frm.set_query('project_code', () => {
            return {
                filters: {
                    project: frm.doc.project
                }
            }
        });
    },

    project(frm) {
        frm.set_value('project_code', null);
    },

    set_pm_user: function (frm) {
        if (frm.doc.employee) {
            return frappe.call({
                method: "hrms.hr.doctype.business_trip.business_trip.get_pm_user",
                args : {
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
});
