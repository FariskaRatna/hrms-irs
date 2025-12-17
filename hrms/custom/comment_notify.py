import frappe

COMMENTS_TARGET = {
    "Leave Application": {
        "approver_fields": ["leave_approver", "approver"]
    },
    "Overtime":{
        "approver_fields": ["assigned_by"]
    },
    "Business Trip": {
        "approver_fields": ["pm_user"]
    },
    "Loan Application": {
        "approver_fields": ["hrd_user"]
    },
    "Loan Settlement" : {
        "approver_fields": ["hrd_user"]
    },
    "Reimbursement": {
        "approver_fields": ["hrd_user"]
    }
}

def get_user_fullname(user):
    return frappe.db.get_value("User", user, "full_name") or user

def notify_comment(comment, event=None):
    doctype = comment.reference_doctype
    docname = comment.reference_name

    if doctype not in COMMENTS_TARGET:
        return
    
    if comment.comment_type != "Comment":
        return
    
    doc = frappe.get_doc(doctype, docname)
    sender = comment.owner
    recipients = set()

    if doc.owner and doc.owner != sender:
        recipients.add(doc.owner)

    for field in COMMENTS_TARGET[doctype]["approver_fields"]:
        user = getattr(doc, field, None)
        if user and user != sender:
            recipients.add(user)

    if not recipients:
        return
    
    sender_name = get_user_fullname(sender)
    
    for user in recipients:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"{sender_name} comment on {doctype} {docname}",
            "email_content": comment.content or "",
            "for_user": user,
            "document_type": doctype,
            "document_name": docname,
            "type": "Alert"
        }).insert(ignore_permissions=True)

    frappe.sendmail(
        recipients=list(recipients),
        subject=f"[{doctype}] Komentar baru - {docname} oleh {sender_name}",
        message=f"""
            <p>Ada komentar baru pada <b>{doctype} {docname} </b> oleh {sender_name}.</p>
            <hr>
            {comment.content or ""}
            </hr>
            <p>
                <a href="{frappe.utils.get_url_to_form(doctype, docname)}"
                     style="display:inline-block; padding:12px 18px; text-decoration:none; border-radius:10px; border:1px solid #777; background:#fff; color:#111; font-weight:600; font-size:15px;">
                    Buka {doctype}
                </a>
            </p>
        """,
        reference_doctype=doctype,
        reference_name=docname
    )