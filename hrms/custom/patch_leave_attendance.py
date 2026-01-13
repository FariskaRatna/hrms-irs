import frappe

def create_attendance_from_leave(doc, method):
    cat = (getattr(doc, "leave_category", "") or "").strip().lower()

    if cat == "dinas":
        return

    if cat == "izin setengah hari":
        _create_draft_attendance(doc)
        return

    from hrms.hr.doctype.leave_application.leave_application import (
        create_attendance_from_leave as original
    )
    return original(doc, method)


def _create_draft_attendance(leave_doc):
    existing = frappe.db.get_value(
        "Attendance",
        {
            "employee": leave_doc.employee,
            "attendance_date": leave_doc.from_date
        },
        "name"
    )
    if existing:
        frappe.db.set_value("Attendance", existing, "needs_checkin_validation", 1)
        return existing
    
    att = frappe.new_doc("Attendance")
    att.employee = leave_doc.employee
    att.employee_name = getattr(leave_doc, "employee_name", None)
    att.company = leave_doc.company
    att.attendance_date = leave_doc.from_date

    att.status = "Present"
    att.needs_checkin_validation = 1

    if "leave_application_ref" in [d.fieldname for d in att.meta.fields]:
        att.leave_application_ref = leave_doc.name

    att.insert(ignore_permissions=True)
    return att.name



