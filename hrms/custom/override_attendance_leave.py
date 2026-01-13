import frappe
from frappe.utils import add_days, getdate

def override_attendance_leave(doc, method=None):
    start = getdate(doc.from_date)
    end = getdate(doc.to_date)

    cat = (getattr(doc, "leave_category", "") or "").strip().lower()

    for i in range((end - start).days + 1):
        date = add_days(start, i)

        attendance = frappe.get_value(
            "Attendance",
            {"employee": doc.employee, "attendance_date": date}
        )
        if not attendance:
            continue

        at_doc = frappe.get_doc("Attendance", attendance)

        if at_doc.docstatus == 1:
            at_doc.cancel()

        if cat == "dinas":
            frappe.delete_doc("Attendance", attendance, force=1)
            continue

        if cat == "izin setengah hari":
            at_doc.needs_checkin_validation = 1
            at_doc.status = "Present"
            at_doc.leave_application = doc.name
            at_doc.leave_type = doc.leave_type
            at_doc.save(ignore_permissions=True)
            continue

        at_doc.status = "On Leave"
        at_doc.leave_type = doc.leave_type
        at_doc.leave_application = doc.name
        at_doc.save(ignore_permissions=True)
        at_doc.submit()

    frappe.msgprint("Attendance update based on the Leave Application.")
