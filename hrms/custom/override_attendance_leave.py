import frappe
from frappe.utils import add_days, getdate

def override_attendance_leave(doc, method=None):
    start = getdate(doc.from_date)
    end = getdate(doc.to_date)

    leave_for_delete = "Dinas"

    for i in range((end - start).days + 1):
        date = add_days(start, i)
        
        attendance = frappe.get_value(
            "Attendance", 
            { "employee": doc.employee, "attendance_date": date }
        )

        if not attendance:
            continue

        at_doc = frappe.get_doc("Attendance", attendance)

        if at_doc.docstatus == 1:
            at_doc.cancel()

        if doc.leave_category == leave_for_delete:
            frappe.delete_doc("Attendance", attendance, force=1)
        else:
            at_doc.status = "On Leave"
            at_doc.leave_type = "Leave"
            at_doc.save()
            at_doc.submit()


    frappe.msgprint("Attendance update based on the Leave Application.")
