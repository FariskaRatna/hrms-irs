import frappe

def ignore_attendance_check(doc, method=None):
    frappe.flags.ignore_attendance_validation = True
    frappe.flags.ignore_leave_attendance_validation = True
    doc.flags.ignore_validate = True
