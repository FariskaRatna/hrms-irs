import frappe

def sync_project_user_permissions(doc, method):
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
