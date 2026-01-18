import frappe
from frappe.utils import getdate
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class CustomSalarySlip(SalarySlip):

    def calculate_component_amounts(self, component_type=None):
        # PENTING: teruskan argumen ke parent
        super().calculate_component_amounts(component_type)

        # hanya adjust setelah earnings dihitung
        if component_type == "earnings":
            self.adjust_attendance_based_components()
            
    def adjust_attendance_based_components(self):
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

        absent_days = sum(1 for a in attendances if a.status == "Absent")
        allowance_deducted_days = sum(
            1 for a in attendances
            if a.status == "Absent" or a.daily_allowance_deducted
        )

        # simpan
        self.absent_days = absent_days
        self.custom_daily_allowance_deducted_days = allowance_deducted_days

        # === TUNJANGAN HARIAN ===
        designation = frappe.db.get_value("Employee", self.employee, "designation")
        rate = 100000 if designation == "Staff" else 175000 if designation == "Project Manager" else 0

        for e in self.earnings:
            if e.salary_component == "Tunjangan Harian":
                e.amount = max(0, e.amount - (rate * allowance_deducted_days))

        # === GAJI POKOK (ABSENT SAJA) ===
        for e in self.earnings:
            if e.salary_component == "Gaji Pokok":
                daily_rate = e.amount / 20
                e.amount = e.amount - (daily_rate * absent_days)
