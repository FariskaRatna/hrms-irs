import frappe
from frappe.utils import now_datetime, add_to_date, get_url

def _make_token(loan_name: str, action: str, approver_user: str, hours_valid: int = 72) -> str:
    token = frappe.generate_hash(length=40)

    doc = frappe.get_doc({
        "doctype": "Loan Application Email Token",
        "token": token,
        "reference_doctype": "Loan Application",
        "reference_name": loan_name,
        "action": action,
        "approver_user": approver_user,
        "expires_on": add_to_date(now_datetime(), hours=hours_valid),
        "used": 0,
    })

    doc.insert(ignore_permissions=True)
    return token

def build_action_url_loan(loan_name: str, action: str, approver_user: str) -> str:
    token = _make_token(loan_name, action, approver_user)

    return get_url(
        f"/api/method/hrms.custom.email_token.loan_application_email_token.act?name={loan_name}&token={token}"
    )


@frappe.whitelist(allow_guest=True)
def act(name: str, token: str):
    rows = frappe.get_all(
        "Loan Application Email Token",
        filters={
            "token": token,
            "reference_doctype": "Loan Application",
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

    loan = frappe.get_doc("Loan Application", name)

    current = (loan.get("approval_status") or "").strip()
    if current in ("Approved", "Rejected"):
        frappe.throw(f"Loan Application is already {current}.", frappe.PermissionError)

    loan.flags.from_email_action = True
    loan.approval_status = action
    loan.save(ignore_permissions=True)

    frappe.db.sql(
        """
        UPDATE `tabLoan Application Email Token`
        SET used = 1, used_on = %s
        WHERE reference_doctype = %s
          AND reference_name = %s
          AND used = 0
        """,
        (now_datetime(), "Loan Application", name),
    )

    frappe.db.commit()

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = get_url(
        f"/message?title=Success&message=Loan%20Application%20{action}%20saved."
    )
