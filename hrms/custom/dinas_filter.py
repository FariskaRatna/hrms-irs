import frappe

@frappe.whitelist()
def get_dinas_leave_list(doctype, txt, searchfield, start, page_len, filters):
    employee = filters.get("employee")

    return frappe.db.sql("""
        SELECT
            purpose,
            name,
            leave_category,
            from_date,
            to_date
        FROM `tabLeave Application`
        WHERE 
            leave_category = 'Dinas'
            AND employee = %(employee)s
            AND (purpose LIKE %(txt)s OR name LIKE %(txt)s)
        ORDER BY modified DESC
        LIMIT %(start)s, %(page_len)s
    """, {
        "employee": employee,
        "txt": "%" + txt + "%",
        "start": start,
        "page_len": page_len
    })
