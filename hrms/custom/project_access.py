import frappe

# Role yang boleh melihat semua Project (selain Administrator)
SUPER_ROLES = {"System Manager"}
PM_FIELD = "project_manager"


def _is_super(user: str) -> bool:
    if user in ("Administrator", "superadmin"):
        return True
    roles = set(frappe.get_roles(user) or [])
    return bool(roles & SUPER_ROLES)


def has_permission(doc, ptype=None, user=None):
    user = user or frappe.session.user

    # Superuser bypass
    if _is_super(user):
        return True

    # CREATE tetap role-based (jangan diblok)
    if ptype == "create":
        return True

    if not doc:
        return False

    # Project Manager
    if user == getattr(doc, "project_manager", None):
        return True

    # User di list users
    for row in (getattr(doc, "users", None) or []):
        if row.user == user:
            return True

    return False


def permission_query_conditions(user):
    user = user or frappe.session.user

    # Superuser: lihat semua
    if _is_super(user):
        return ""

    # IMPORTANT:
    # Sesuaikan nama child table dan field user jika berbeda.
    # Default ERPNext: child doctype "Project User" -> table "tabProject User", field "user"
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
