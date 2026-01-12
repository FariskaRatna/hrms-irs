import frappe

def has_permission(doc, ptype=None, user=None):
    user = user or frappe.session.user

    # CREATE → role-based (Project Manager boleh create)
    if ptype == "create":
        return True

    if not doc:
        return False

    # Project Manager
    if user == getattr(doc, "project_manager", None):
        return True

    # User di child table Project.users
    for row in (getattr(doc, "users", None) or []):
        if row.user == user:
            return True

    return False


def permission_query_conditions(user):
    user = user or frappe.session.user

    return f"""
        (
            `tabProject`.project_manager = '{user}'
            OR EXISTS (
                SELECT 1
                FROM `tabProject User` pu
                WHERE pu.parent = `tabProject`.name
                AND pu.user = '{user}'
            )
        )
    """
