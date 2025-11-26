import frappe

def prevent_attendance_for_dinas(doc, method):
    # Ambil leave application yang terkait attendance ini
    allowed_roles = ["HR Manager", "HR User", "System Manager", "Administrator"]
    user_roles = frappe.get_roles(frappe.session.user)
    if any(role in user_roles for role in allowed_roles):
        return

    if getattr(frappe.flags, "ignore_dinas_block", False):
        return
    
    if getattr(frappe.flags, "force_attendance_present", False):
        return
        
    leave = frappe.db.get_value(
        "Leave Application",
        {"employee": doc.employee, "from_date": ["<=", doc.attendance_date], "to_date": [">=", doc.attendance_date]},
        ["leave_category"],
        as_dict=True
    )

    # Kalau leave category = Dinas → blokir creation
    if leave and leave.leave_category == "Dinas":
        frappe.throw("Attendance is not created for Dinas leave.")
