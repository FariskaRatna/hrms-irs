import frappe
from frappe.utils import now_datetime, add_to_date, get_url
from frappe import _

def _make_token(reim_name: str, action: str, approver_user: str, hours_valid: int = 72) -> str:
    token = frappe.generate_hash(length=40)

    doc = frappe.get_doc({
        "doctype": "Reimbursement Email Token",
        "token": token,
        "reference_doctype": "Reimbursement",
        "reference_name": reim_name,
        "action": action,
        "approver_user": approver_user,
        "expires_on": add_to_date(now_datetime(), hours=hours_valid),
        "used": 0,
    })

    doc.insert(ignore_permissions=True)
    return token

def build_action_url_reimburse(reim_name: str, action: str, approver_user: str) -> str:
    token = _make_token(reim_name, action, approver_user)

    return get_url(
        f"/api/method/hrms.custom.email_token.reimbursement_email_token.act?name={reim_name}&token={token}"
    )


@frappe.whitelist(allow_guest=True)
def act(name: str, token: str):
    rows = frappe.get_all(
        "Reimbursement Email Token",
        filters={
            "token": token,
            "reference_doctype": "Reimbursement",
            "reference_name": name
        },
        fields=["name", "action", "approver_user", "expires_on", "used"],
        limit=1
    )

    if not rows:
        frappe.throw("Invalid Link", frappe.PermissionError)

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

    reim = frappe.get_doc("Reimbursement", name)

    current = (reim.get("approval_status") or "").strip()
    if current in ("Approved", "Rejected"):
        frappe.throw(_("Reimbursement is already {0}").format(frappe.bold(current)), frappe.PermissionError)

    reim.flags.from_email_action = True
    reim.approval_status = action
    reim.save(ignore_permissions=True)

    frappe.db.sql(
        """
        UPDATE `tabReimbursement Email Token`
        SET used = 1, used_on = %s
        WHERE reference_doctype = %s
          AND reference_name = %s
          AND used = 0
        """,
        (now_datetime(), "Reimbursement", name),
    )

    frappe.db.commit()

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = get_url(
        f"/message?title=Success&message=Reimbursement%20{action}%20saved."
    )
