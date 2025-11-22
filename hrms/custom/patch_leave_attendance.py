import frappe

def create_attendance_from_leave(doc, method):
    # Skip khusus leave kategori Dinas
    if getattr(doc, "leave_category", None) == "Dinas":
        return  # submit jalan, attendance tidak dibuat

    # Jalankan fungsi bawaan HRMS
    from hrms.hr.doctype.leave_application.leave_application import (
        create_attendance_from_leave as original
    )
    return original(doc, method)
