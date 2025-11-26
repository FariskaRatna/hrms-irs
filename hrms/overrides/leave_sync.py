import frappe
from frappe.utils import getdate
import datetime

def handle_leave_sync(doc, method):
    employee = doc.employee
    start = getdate(doc.from_date)
    end = getdate(doc.to_date)

    current = start
    while current <= end:
        update_attendance(employee, current, doc)
        current = frappe.utils.add_days(current, 1)

def update_attendance(employee, date, leave_doc):
    att = frappe.db.exists("Attendance", {"employee": employee, "attendance_date": date})

    today = date.today()
    start_ref = datetime.date(today.year, today.month, 21)
    end_ref = datetime.date(
        today.year + (1 if today.month == 12 else 0),
        1 if today.month == 12 else today.month + 1,
        20
    )

    if att:
        attendance = frappe.get_doc("Attendance", att)
        attendance.leave_type = "Leave"
        attendance.leave_application = leave_doc.name
        if leave_doc.leave_category == "Cuti":
            attendance.status = "On Leave"
            attendance.daily_allowance_deducted = True
            attendance.attendance_reason = "Cuti"
        elif leave_doc.leave_category == "Izin":
            attendance.status = "On Leave"
            attendance.daily_allowance_deducted = True
            attendance.attendance_reason = "Izin"
        elif leave_doc.leave_category == "Sakit":
            if leave_doc.doctor_note:
                attendance.status = "Present"
                attendance.daily_allowance_deducted = False
                attendance.attendance_reason = "Sakit dengan Surat Dokter"
            else:
                attendance.status = "On Leave"
                attendance.daily_allowance_deducted = True
                attendance.attendance_reason = "Sakit tanpa Surat Dokter"
        elif leave_doc.leave_category == "Setengah Hari":
            half_day_count = frappe.db.count(
                "Leave Application",
                filters={
                    "employee": employee,
                    "leave_category": "Setengah Hari",
                    "from_date": ["between", [start_ref, end_ref]],
                    "docstatus": 1
                }
            )
            if half_day_count <= 2:
                attendance.status = "Present"
                attendance.daily_allowance_deducted = False
                attendance.attendance_reason = "Setengah Hari (kurang dari 2 kali)"
            else:
                attendance.status = "On Leave"
                attendance.daily_allowance_deducted = True
                attendance.attendance_reason = "Setengah Hari (lebih dari 2 kali)"
        attendance.save()
        frappe.db.commit()
        return

# ini bentar dulu

# def undo_leave_sync(doc, method):
#     employee = doc.employee
#     start = getdate(doc.from_date)
#     end = getdate(doc.to_date)

#     current = start
#     while current <= end:
#         att = frappe.db.exists(
#             "Attendance",
#             {
#                 "employee": employee,
#                 "attendance_date": current,
#                 "leave_application": doc.name
#             }
#         )

#         if att:


