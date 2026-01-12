import frappe

def allow_create_bypass_user_permissions(doc, method=None):
    # Hanya saat insert dokumen baru
    frappe.flags.ignore_user_permissions = True

def sync_project_user_permissions(doc, method=None):
    users = set()

    if getattr(doc, "project_manager", None):
        users.add(doc.project_manager)

    for row in (doc.users or []):
        if row.user:
            users.add(row.user)

    frappe.db.delete("User Permission", {"allow": "Project", "for_value": doc.name})

    for user in users:
        frappe.get_doc({
            "doctype": "User Permission",
            "user": user,
            "allow": "Project",
            "for_value": doc.name,
            "apply_to_all_doctypes": 1,
        }).insert(ignore_permissions=True)

def set_default_project_manager(doc, method=None):
    if not getattr(doc, "project_manager", None):
        doc.project_manager = frappe.session.user
