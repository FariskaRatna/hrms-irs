import frappe

ALLOWED_ROLES = ["Administrator", "HR Manager", "HR User", "Project Manager", "System Manager"]

def prevent_edit_after_approved(doc, event):
    if not hasattr(doc, "status"):
        return

    if doc.status != "Approved":
        return

    if doc.is_new():
        return
    
    current_user = frappe.session.user
    user_roles = frappe.get_roles(current_user)
    if any(role in user_roles for role in ALLOWED_ROLES):
        return

    if current_user == doc.owner:
        frappe.throw("This document has been approved and can no longer be edited by the requester.")