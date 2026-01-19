import frappe
from frappe.utils import getdate
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class CustomSalarySlip(SalarySlip):

    def calculate_net_pay(self):
        super().calculate_net_pay()
        self.adjust_attendance_effects()

    def adjust_attendance_effects(self):
        if not self.employee or not self.start_date or not self.end_date:
            return

        start = getdate(self.start_date)
        end = getdate(self.end_date)

        attendances = frappe.get_all(
            "Attendance",
            filters={
                "employee": self.employee,
                "attendance_date": ["between", [start, end]],
                "docstatus": 1
            },
            fields=["status", "daily_allowance_deducted"]
        )

        total_days = len(attendances)

        absent_days = sum(1 for a in attendances if a.status == "Absent")
        allowance_deducted_days = sum(1 for a in attendances if a.daily_allowance_deducted)

        payment_days = max(total_days - allowance_deducted_days, 0)

        self.absent_days = absent_days
        self.custom_daily_allowance_deducted_days = allowance_deducted_days

        designation = frappe.db.get_value("Employee", self.employee, "designation")
        allowance_rate = 100000 if designation == "Staff" else 175000 if designation == "Project Manager" else 0

        allowance_amount = allowance_rate * payment_days

        basic_adjustment = 0
        for e in self.earnings:
            if e.salary_component == "Gaji Pokok":
                base_amount = e.default_amount or e.amount
                daily_rate = base_amount / 20
                basic_adjustment = daily_rate * absent_days
                e.amount = base_amount - basic_adjustment

            if e.salary_component == "Tunjangan Harian":
                e.amount = allowance_amount

        # === KUNCI UTAMA ===
        self.gross_pay = sum(e.amount for e in self.earnings)
        self.net_pay = self.gross_pay - self.total_deduction
