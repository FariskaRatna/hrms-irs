import frappe
from frappe.utils import getdate, rounded, flt
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class CustomSalarySlip(SalarySlip):

    def validate(self):
        """Override validate dengan proteksi manual override"""
        
        # STEP 1: Simpan semua perubahan manual SEBELUM parent validate
        self.preserve_manual_overrides()
        
        # STEP 2: Panggil parent validate (ini akan recalculate semua)
        super().validate()
        
        # STEP 3: RESTORE nilai manual override yang sudah disimpan
        self.restore_manual_overrides()
        
        # STEP 4: Jalankan custom attendance adjustment (skip yang manual override)
        if self.earnings:
            self.store_default_amounts()
            self.adjust_attendance_effects()
            self.recalculate_totals()

    def preserve_manual_overrides(self):
        """Simpan nilai manual override SEBELUM parent validate menimpanya"""
        # Simpan di temporary variable (tidak persistent ke DB)
        self._manual_earnings = {}
        self._manual_deductions = {}
        
        # Simpan earning yang di-override manual
        for e in self.earnings:
            if e.get("is_manual_override") == 1 or e.get("is_manual_override") is True:
                # Simpan dengan key salary_component untuk restore nanti
                self._manual_earnings[e.salary_component] = {
                    'amount': e.amount,
                    'default_amount': e.get('default_amount')
                }
        
        # Simpan deduction yang di-override manual
        for d in self.deductions:
            if d.get("is_manual_override") == 1 or d.get("is_manual_override") is True:
                self._manual_deductions[d.salary_component] = {
                    'amount': d.amount,
                    'default_amount': d.get('default_amount')
                }

    def restore_manual_overrides(self):
        """RESTORE nilai manual override SETELAH parent validate"""
        # Restore earnings yang di-override manual
        if hasattr(self, '_manual_earnings'):
            for e in self.earnings:
                if e.salary_component in self._manual_earnings:
                    saved = self._manual_earnings[e.salary_component]
                    e.amount = saved['amount']
                    e.is_manual_override = 1
                    if saved.get('default_amount'):
                        e.default_amount = saved['default_amount']
        
        # Restore deductions yang di-override manual
        if hasattr(self, '_manual_deductions'):
            for d in self.deductions:
                if d.salary_component in self._manual_deductions:
                    saved = self._manual_deductions[d.salary_component]
                    d.amount = saved['amount']
                    d.is_manual_override = 1
                    if saved.get('default_amount'):
                        d.default_amount = saved['default_amount']

    def store_default_amounts(self):
        """Simpan nilai default untuk tracking perubahan manual"""
        for e in self.earnings:
            # Jangan overwrite default_amount jika sudah ada
            if not e.get("default_amount") and e.amount > 0:
                e.default_amount = e.amount
        
        for d in self.deductions:
            if not d.get("default_amount") and d.amount > 0:
                d.default_amount = d.amount

    def recalculate_totals(self):
        """Recalculate totals"""
        self.gross_pay = sum(e.amount for e in self.earnings)
        self.total_deduction = sum(d.amount for d in self.deductions)
        self.net_pay = self.gross_pay - self.total_deduction
        self.set_rounded_total()
        self.set_net_total_in_words()

    def set_rounded_total(self):
        if self.is_rounding_total_disabled():
            self.rounded_total = self.net_pay
            self.base_rounded_total = self.base_net_pay
        else:
            self.rounded_total = rounded(self.net_pay, 0)

        if self.currency == frappe.get_cached_value("Company", self.company, "default_currency"):
            self.base_rounded_total = self.rounded_total
        else:
            self.base_rounded_total = rounded(
                flt(self.rounded_total * self.exchange_rate),
                self.precision("base_rounded_total")
            )

    def adjust_attendance_effects(self):
        """Hitung attendance effects dengan respect manual override"""
        
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

        if not attendances:
            return

        total_days = len(attendances)
        absent_days = sum(1 for a in attendances if a.status == "Absent")
        allowance_deducted_days = sum(1 for a in attendances if a.daily_allowance_deducted)
        payment_days = max(total_days - allowance_deducted_days, 0)

        self.absent_days = absent_days
        self.custom_daily_allowance_deducted_days = allowance_deducted_days

        designation = frappe.db.get_value("Employee", self.employee, "designation")
        allowance_rate = 100000 if designation == "Staff" else 175000 if designation == "Project Manager" else 0
        allowance_amount = allowance_rate * payment_days

        # Process earnings - SKIP yang manual override
        for e in self.earnings:
            # CRITICAL: Cek manual override
            if e.get("is_manual_override") == 1 or e.get("is_manual_override") is True:
                continue

            # Simpan default amount jika belum ada
            if not e.get("default_amount") and e.amount > 0:
                e.default_amount = e.amount

            if e.salary_component == "Gaji Pokok":
                base_amount = e.default_amount if e.get("default_amount") else e.amount
                if base_amount > 0:
                    daily_rate = base_amount / 20
                    basic_adjustment = daily_rate * absent_days
                    e.amount = base_amount - basic_adjustment

            elif e.salary_component == "Tunjangan Harian":
                e.amount = allowance_amount

        # Process deductions - SKIP yang manual override
        for d in self.deductions:
            if d.get("is_manual_override") == 1 or d.get("is_manual_override") is True:
                continue
            
            if not d.get("default_amount") and d.amount > 0:
                d.default_amount = d.amount