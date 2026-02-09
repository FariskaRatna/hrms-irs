import frappe

def execute(filters=None):
    filters = filters or {}

    employee = filters.get("employee")
    department = filters.get("department")

    conditions = ["leave_category = 'Dinas'"]
    values = {}

    if employee:
        conditions.append("employee = %(employee)s")
        values["employee"] = employee
    if department:
        conditions.append("department = %(department)s")
        values["department"] = department

    condition_sql = " AND ".join(conditions)

    data = frappe.db.sql(f"""
        SELECT
            destination,
            COUNT(name) AS total_dinas
        FROM `tabLeave Application`
        WHERE {condition_sql}
        GROUP BY destination
        ORDER BY total_dinas DESC
    """, values, as_dict=True)

    columns = [
        {"label": "Destination", "fieldname": "destination", "fieldtype": "Data"},
        {"label": "Total Dinas", "fieldname": "total_dinas", "fieldtype": "Int"}
    ]

    chart = {
        "data": {
            "labels": [d["destination"] for d in data],
            "datasets": [{
                "name": "Total Dinas",
                "values": [d["total_dinas"] for d in data],
            }]
        },
        "type": "bar"
    }

    return columns, data, None, chart
