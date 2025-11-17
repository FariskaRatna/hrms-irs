import frappe

def prevent_edit_after_approved(doc, event):
    if not hasattr(doc, "status"):
        return

    if doc.status != "Approved":
        return

    if doc.is_new():
        return
    
    current_user = frappe.session.user

    if current_user != doc.owner:
        return
    
    frappe.throw("This document has been approved and can no longer be edited by the requester.")