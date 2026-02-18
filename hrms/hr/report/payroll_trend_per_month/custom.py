import frappe
from datetime import date
from dateutil.relativedelta import relativedelta

def execute(filters=None):

    # 12 bulan ke belakang dari hari ini
    today = date.today().replace(day=1)
    start = today - relativedelta(months=11)

    payroll_map = {}

    rows = frappe.db.sql("""
        SELECT
            DATE_FORMAT(end_date, '%%Y-%%m') as ym,
            SUM(net_pay) as total
        FROM `tabSalary Slip`
        WHERE end_date >= %s
        AND docstatus = 1
        GROUP BY ym
        ORDER BY ym
    """, (start,), as_dict=True)

    for r in rows:
        payroll_map[r.ym] = r.total

    # generate semua bulan biar tidak bolong
    labels = []
    values = []
    data = []

    cursor = start
    for i in range(12):
        ym = cursor.strftime("%Y-%m")
        label = cursor.strftime("%b %Y")

        value = payroll_map.get(ym, 0)

        labels.append(label)
        values.append(value)

        data.append({
            "month": label,
            "payroll": value
        })

        cursor += relativedelta(months=1)

    columns = [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
        {"label": "Payroll", "fieldname": "payroll", "fieldtype": "Currency", "width": 180},
    ]

    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Payroll",
                    "values": values
                }
            ]
        },
        "type": "line"
    }

    return columns, data, None, chart
