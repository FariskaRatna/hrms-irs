// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime", {
    refresh(frm) {
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

    async set_employee(frm) {
        if (frm.doc.employee) return;

        const employee = await hrms.get_current_employee(frm);
        if (employee) {
            frm.set_value("employee", employee);
        }
    },

    employee(frm) {
        if (!frm.doc.employee) return;

        frappe.db.get_value("Employee", frm.doc.employee, ["pm_user"])
            .then(r => {
                frm.set_value("pm_user", r.message.pm_user);
            });
    }
});

