import frappe

def prevent_attendance_for_dinas(doc, method):
    # Ambil leave application yang terkait attendance ini
    leave = frappe.db.get_value(
        "Leave Application",
        {"employee": doc.employee, "from_date": ["<=", doc.attendance_date], "to_date": [">=", doc.attendance_date]},
        ["leave_category"],
        as_dict=True
    )

    # Kalau leave category = Dinas → blokir creation
    if leave and leave.leave_category == "Dinas":
        frappe.throw("Attendance is not created for Dinas leave.")
