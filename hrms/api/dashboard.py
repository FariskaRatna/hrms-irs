import frappe

@frappe.whitelist()
def get_hr_announcements():
    announcements = frappe.get_all(
        "Note",
        fields=["name", "title", "content"],
        filters={"public": 1},
        order_by="creation desc",
        limit=5
    )
    return announcements
