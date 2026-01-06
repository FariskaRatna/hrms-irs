import frappe
from frappe.utils import getdate, format_date
from hrms.hr.doctype.attendance.attendance import Attendance as HRMSAttendance
from frappe import _


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
            & (LeaveApplication.approval_status == "Approved")
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
            self.attendance_reason = "Dinas"

            frappe.msgprint(
                _("Attendance: {0} is marked Present (Dinas) on {1}").format(
                    frappe.bold(self.employee_name),
                    frappe.bold(format_date(self.attendance_date))
                ),
                indicator="green"
            )
            return
        
        if d.leave_category == "Izin Setengah Hari":
            self.status = "Present"
            self.leave_type = "Leave"
            self.leave_application = d.name

            frappe.msgprint(
                _("Attendance: {0} is marked Present (Izin Setengah Hari) on {1}").format(
                    frappe.bold(self.employee_name),
                    frappe.bold(format_date(self.attendance_date))
                ),
                indicator="green"
            )

            return

        # Normal leave
        self.leave_type = d.leave_type
        self.leave_application = d.name

        if d.half_day_date == getdate(self.attendance_date):
            self.status = "Half Day"
            frappe.msgprint(
                _("Attendance: {0} is marked Half Day on {1}").format(
                    frappe.bold(self.employee_name),
                    frappe.bold(format_date(self.attendance_date))
                ),
                indicator="yellow"
            )
        else:
            self.status = "On Leave"
            frappe.msgprint(
                _("Leave detected for {0} on {1} — attendance not created").format(
                    frappe.bold(self.employee_name),
                    frappe.bold(format_date(self.attendance_date))
                ),
                indicator="red"
            )
