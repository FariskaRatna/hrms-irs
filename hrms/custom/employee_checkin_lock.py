import frappe
from frappe import _

ALLOWED_ROLES = ["Administrator", "HR Manager", "System Manager"]

def lock_employee_checkin(doc, method=None):
    if getattr(doc, "locked", 0):
        return
    
    frappe.db.set_value(doc.doctype, doc.name, "locked", 1, update_modified=False)

def prevent_edit_if_locked(doc, method=None):
    if doc.is_new():
        return
    
    locked = frappe.db.get_value(doc.doctype, doc.name, "locked") or 0
    if not locked:
        return
    
    current_user = frappe.session.user
    user_roles = frappe.get_roles(current_user)
    if any(role in user_roles for role in ALLOWED_ROLES):
        return
    
    frappe.throw(_("This Employee Check-in record is locked and cannot be edited."))