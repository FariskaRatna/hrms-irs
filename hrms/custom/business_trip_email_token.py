import frappe
from frappe.utils import now_datetime, add_to_date, get_url

def _make_token(bt_name: str, action: str, approver_user: str, hours_valid: int = 48) -> str:
    token = frappe.generate_hash(length=40)

    doc =  frappe.get_doc({
        "doctype": "Business Trip Email Token",
        "token": token,
        "reference_doctype": "Business Trip",
        "reference_name": bt_name,
        "action": action,
        "approver_user": approver_user,
        "expires_on": add_to_date(now_datetime(), hours=hours_valid),
        "used": 0,
    })
    doc.insert(ignore_permissions=True)

    return token

def build_action_url(bt_name: str, action: str, approver_user: str) -> str:
    token = _make_token(bt_name, action, approver_user)

    return get_url(
        f"/api/method/hrms.custom.business_trip_email_token.act?name={bt_name}&token={token}"
    )

@frappe.whitelist(allow_guest=True)
def act(name: str, token: str):
    rows = frappe.get_all(
        "Business Trip Email Token",
        filters={
            "token": token,
            "reference_doctype": "Business Trip",
            "reference_name": name
        },
        fields=["name", "action", "approver_user", "expires_on", "used"],
        limit=1
    )

    if not rows:
        frappe.throw("Invalid link.", frappe.PermissionError)

    t = rows[0]

    if int(t.get("used") or 0) == 1:
        frappe.throw("This link has already been used.", frappe.PermissionError)

    expires_on = t.get("expires_on")
    if not expires_on:
        frappe.throw("Token expiry is missing.", frappe.PermissionError)

    if now_datetime() > expires_on:
        frappe.throw("This link has expired.", frappe.PermissionError)

    action = t.get("action")
    if action not in ("Approved", "Rejected"):
        frappe.throw("Invalid action.", frappe.PermissionError)

    bt = frappe.get_doc("Business Trip", name)

    current = (bt.get("approval_status") or "").strip()
    if current in ("Approved", "Rejected"):
        frappe.throw(f"Business Trip is already {current}.", frappe.PermissionError)

    bt.flags.from_email_action = True
    bt.approval_status = action
    bt.save(ignore_permissions=True)

    frappe.db.sql(
        """
        UPDATE `tabBusiness Trip Email Token`
        SET used = 1, used_on = %s
        WHERE reference_doctype = %s
          AND reference_name = %s
          AND used = 0
        """,
        (now_datetime(), "Business Trip", name),
    )

    frappe.db.commit()

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = get_url(
        f"/message?title=Success&message=Business%20Trip%20{action}%20saved."
    )
