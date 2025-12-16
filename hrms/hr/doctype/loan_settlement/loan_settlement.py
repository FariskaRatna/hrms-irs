# Copyright (c) 2025
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import get_fullname
from hrms.utils import get_employee_email
from hrms.custom.email_token.loan_settlement_email_token import build_action_url_loan_set

class LoanSettlement(Document):
    def validate(self):
        if not self.loan:
            frappe.throw("Please select a Loan")

        loan = frappe.get_doc("Loan", self.loan)
        employee = frappe.get_doc("Employee", self.employee)

        new_balance = (loan.balance_amount or 0) - (self.amount or 0)

        if new_balance < 0:
            frappe.throw("Payment amount exceeds remaining loan balance")

        self.remaining_balance = new_balance

    def on_update(self):
        if self.approval_status == "Pending" and self.docstatus < 1:
            if frappe.db.get_single_value("HR Settings", "send_loan_settlement_application_notification"):
                self.notify_hrd()

        if self.approval_status in ["Approved", "Rejected"] and self.docstatus < 1:
            if frappe.db.get_single_value("HR Settings", "send_loan_settlement_application_notification"):
                if getattr(self.flags, "from_email_action", False):
                    self.notify_employee(sender_email=self.get_email_hrd())
                else:
                    self.notify_employee(sender_email=self.get_email_hrd())

    def on_submit(self):
        if self.approval_status in ["Pending"]:
            frappe.throw(_("Only Loan Settlement with approval status 'Approved' and 'Rejected' can be submitted"))

        if frappe.db.get_single_value("HR Settings", "send_loan_settlement_application_notification"):
            self.notify_employee()
            if self.approval_status == "Approved":
                self.create_loan_settlement()
    
    def on_cancel(self):
        if frappe.db.get_single_value("HR Settings", "send_loan_settlement_application_notification"):
            self.notify_employee()

    def create_loan_settlement(self):
        loan = frappe.get_doc("Loan", self.loan)
        employee = frappe.get_doc("Employee", self.employee)

        loan.balance_amount = (loan.balance_amount or 0) - (self.amount or 0)

        if loan.installment and self.amount >= loan.installment:
            loan.paid_installments += int(self.amount / loan.installment)

        if loan.balance_amount <= 0:
            loan.repayment_status = "Paid"
            loan.status = "Closed"
            frappe.msgprint(f"Loan {loan.name} has been fully settled.")
        else:
            frappe.msgprint(f"Loan {loan.name} has been partially settled. Remaining balance: {loan.balance_amount}")

        repayment = loan.append("repayment_tracking", {})
        repayment.payment_date = self.settlement_date
        repayment.amount_paid = self.amount
        repayment.balance_after = loan.balance_amount
        repayment.reference = self.name
        repayment.remarks = "Loan Settlement Payment"
        
        loan.save(ignore_permissions=True)

        # Update saldo di Employee
        employee.loan_balance = (employee.loan_balance or 0) - (self.amount or 0)
        if employee.loan_balance < 0:
            employee.loan_balance = 0
        employee.save(ignore_permissions=True)

    def get_requester(self):
        user_id = frappe.db.get_value("Employee", self.employee, "user_id") or self.owner
        return frappe.get_value("User", user_id, "email")

    def get_email_hrd(self):
        if self.hrd_user:
            return frappe.get_value("User", self.hrd_user, "email")
        return None

    def notify_hrd(self):
        if not self.hrd_user:
            return
        
        parent_doc = frappe.get_doc("Loan Settlement", self.name)
        approver_user = self.hrd_user or parent_doc.owner
        args = parent_doc.as_dict()

        args.update({
			"approve_url": build_action_url_loan_set(
				parent_doc.name,
				"Approved",
				approver_user
			),
			"reject_url": build_action_url_loan_set(
				parent_doc.name,
				"Rejected",
				approver_user
			),
		})

        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"Loan Settlement Request {self.employee_name} Requires Your Approval",
            "email_content": f"Employee {self.employee_name} submitted loan settlement and requires your approval.",
            "for_user": self.hrd_user,
            "type": "Alert",
            "document_type": "Loan Settlement",
            "document_name": self.name
        }).insert(ignore_permissions=True)

        template = frappe.db.get_single_value("HR Settings", "loan_settlement_request_notification_template")
        if not template:
            frappe.msgprint(_("Please set default template for Loan Settlement Request Notification in HR Settings."))
            return
        email_template = frappe.get_doc("Email Template", template)
        subject = frappe.render_template(email_template.subject, args)
        message = frappe.render_template(email_template.response_, args)
        attachments = get_doc_attachments("Loan Settlement", self.name)

        self.notify(
            {
                "message": message,
                "message_to": self.hrd_user,
                "subject": subject,
                "sender_email": self.get_requester(),
                "attachments": attachments,
            }
        )


    def notify_employee(self, sender_email=None):
        employee_email = get_employee_email(self.employee)

        if not employee_email:
            return

        employee_user = frappe.db.get_value("Employee", self.employee, "user_id")

        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"Loan Settlement Request {self.approval_status}",
            "email_content": f"Your loan settlement request has been {self.approval_status}.",
            "for_user": employee_user,
            "type": "Alert",
            "document_type": "Loan Settlement",
            "document_name": self.name
        }).insert(ignore_permissions=True)
        
        parent_doc = frappe.get_doc("Loan Settlement", self.name)
        args = parent_doc.as_dict()

        template = frappe.db.get_single_value("HR Settings", "loan_settlement_status_notification_template")
        if not template:
            frappe.msgprint(_("Please set default template for Loan Settlement Status Notification in HR Settings."))
            return
        email_template = frappe.get_doc("Email Template", template)
        subject = frappe.render_template(email_template.subject, args)
        message = frappe.render_template(email_template.response_, args)

        self.notify(
            {
                "message": message,
                "message_to": employee_email,
                "subject": subject,
                "notify": "employee",
                "sender_email": sender_email,
            }
        )

    def notify(self, args):
        args = frappe._dict(args)
        contact = args.message_to
        if not isinstance(contact, list):
            if not args.notify == "employee":
                contact = frappe.get_doc("User", contact).email or contact

        sender_email = args.get("sender_email")
        if not sender_email:
            sender_email = frappe.get_doc("User", frappe.session.user).email

        attachments = args.get("attachments") or []

        try:
            frappe.sendmail(
                recipients=contact,
                sender=sender_email,
                subject=args.subject,
                message=args.message,
                attachments=attachments,
            )
            frappe.msgprint(_("Email sent to {0}").format(contact))
        except frappe.OngoingEmailError:
            pass


def get_doc_attachments(doctype: str, name: str):
	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": doctype,
			"attached_to_name": name,
			"is_folder": 0,
		},
		fields=["file_name", "file_url"],
		order_by="creation asc"
	)

	attachments = []
	for f in files:
		if not f.get("file_url"):
			continue
		attachments.append({
			"file_url": f["file_url"],
			"fname": f.get("file_name") or "attachment"
		})
	
	return attachments
