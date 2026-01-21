import frappe
from frappe.utils import getdate, add_days

def sync_for_leave(leave_name):
    leave = frappe.get_doc("Leave Application", leave_name)
    category = (leave.leave_category or "").strip().lower()

    if category == "dinas":
        return
    
    start = getdate(leave.from_date)
    end = getdate(leave.to_date)

    for i in range((end - start).days + 1):
        att_date = add_days(start, i)
        _sync_day(leave, att_date, category)

    frappe.db.commit()

def _sync_day(leave, att_date, category):
    existing = frappe.db.get_value(
        "Attendance",
        {
            "employee": leave.employee,
            "attendance_date": att_date
        },
        "name"
    )

    attendance = (
        frappe.get_doc("Attendance", existing)
        if existing
        else frappe.new_doc("Attendance")
    )

    attendance.employee = leave.employee
    attendance.employee_name = leave.employee_name
    attendance.company = leave.company
    attendance.attendance_date = att_date

    if category == "izin setengah hari":
        attendance.status = "Present"
    else:
        if leave.half_day and leave.half_day_date == att_date:
            attendance.status = "Half Day"
        else:
            attendance.status = "On Leave"

    attendance.leave_type = leave.leave_type
    attendance.leave_application = leave.name

    attendance.save(ignore_permissions=True)