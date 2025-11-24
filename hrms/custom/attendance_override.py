import frappe
from frappe.utils import getdate, format_date
from hrms.hr.doctype.attendance.attendance import Attendance as HRMSAttendance


class CustomAttendance(HRMSAttendance):
    def check_leave_record(self):
        return custom_check_leave_record(self)


def custom_check_leave_record(self):
    LeaveApplication = frappe.qb.DocType("Leave Application")
    leave_record = (
        frappe.qb.from_(LeaveApplication)
        .select(
            LeaveApplication.leave_type,
            LeaveApplication.half_day,
            LeaveApplication.half_day_date,
            LeaveApplication.name,
            LeaveApplication.leave_category,
        )
        .where(
            (LeaveApplication.employee == self.employee)
            & (self.attendance_date >= LeaveApplication.from_date)
            & (self.attendance_date <= LeaveApplication.to_date)
            & (LeaveApplication.status == "Approved")
            & (LeaveApplication.docstatus == 1)
        )
    ).run(as_dict=True)

    if not leave_record:
        return

    for d in leave_record:

        # CASE: Dinas (override jadi Present)
        if d.leave_category == "Dinas":
            self.status = "Present"
            self.leave_type = "Leave"
            self.leave_application = d.name
            self.attendance_reason = "Hadir"

            frappe.msgprint(
                f"Attendance: {self.employee_name} is marked Present (Dinas) on {format_date(self.attendance_date)}",
                indicator="green"
            )
            return

        # Normal leave
        self.leave_type = d.leave_type
        self.leave_application = d.name

        if d.half_day_date == getdate(self.attendance_date):
            self.status = "Half Day"
            frappe.msgprint(
                f"{self.employee_name} is marked Half Day on {format_date(self.attendance_date)}",
                indicator="yellow"
            )
        else:
            self.status = "On Leave"
            frappe.msgprint(
                f"Leave detected for {self.employee_name} on {format_date(self.attendance_date)} — attendance not created.",
                indicator="red"
            )
