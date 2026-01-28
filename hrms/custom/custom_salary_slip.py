import frappe
from frappe.utils import getdate, rounded, flt
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class CustomSalarySlip(SalarySlip):

    def validate(self):
        """Override validate dengan proteksi manual override"""
        self.preserve_manual_overrides()
        super().validate()
        self.restore_manual_overrides()

        if self.earnings:
            self.store_default_amounts()
            self.adjust_attendance_effects()
            self.calculate_zakat()
            self.recalculate_totals()

    def calculate_zakat(self, max_iterations=5, tolerance=1):
        zakat_row = None
        for d in self.deductions:
            if d.salary_component == "Potongan Zakat":
                zakat_row = d
                break

        if not zakat_row:
            return
        
        if zakat_row.get("is_manual_override") == 1 or zakat_row.get("is_manual_override") is True:
            return
        
        assignment = frappe.get_all(
            "Salary Structure Assignment",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "from_date": ["<=", self.start_date]
            },
            fields=["zakat_mode", "zakat_amount", "zakat_percentage"],
            order_by="from_date desc",
            limit=1
        )

        if not assignment:
            zakat_row.amount = 0
            return
        
        zakat_mode = assignment[0].get("zakat_mode") or ""
        zakat_amount = assignment[0].get("zakat_amount") or 0
        zakat_percentage = assignment[0].get("zakat_percentage") or 0

        if zakat_mode == "":
            zakat_row.amount = 0
        elif zakat_mode == "Fixed Amount":
            zakat_row.amount = zakat_amount
        elif zakat_mode != "Percentage":
            zakat_row.amount = 0
            return
        
        previous_zakat = 0

        for i in range(max_iterations):
            gross_pay = sum(e.amount for e in self.earnings)
            total_deduction_no_zakat = sum(
                d.amount for d in self.deductions 
                if d.salary_component != "Potongan Zakat"
            )
            net_pay_before_zakat = gross_pay - total_deduction_no_zakat

            new_zakat = (0.34 * (zakat_percentage / 100)) * net_pay_before_zakat

            if abs(new_zakat - previous_zakat) < tolerance:
                zakat_row.amount = round(new_zakat, 2)
                break

            zakat_row.amount = new_zakat
            previous_zakat = new_zakat

        if zakat_row.amount < 0:
            zakat_row.amount = 0
        

    def preserve_manual_overrides(self):
        """Simpan nilai manual override SEBELUM parent validate menimpanya"""
        self._manual_earnings = {}
        self._manual_deductions = {}
        
        for e in self.earnings:
            if e.get("is_manual_override") == 1 or e.get("is_manual_override") is True:
                self._manual_earnings[e.salary_component] = {
                    'amount': e.amount,
                    'default_amount': e.get('default_amount')
                }

        for d in self.deductions:
            if d.get("is_manual_override") == 1 or d.get("is_manual_override") is True:
                self._manual_deductions[d.salary_component] = {
                    'amount': d.amount,
                    'default_amount': d.get('default_amount')
                }

    def restore_manual_overrides(self):
        """RESTORE nilai manual override SETELAH parent validate"""
        if hasattr(self, '_manual_earnings'):
            for e in self.earnings:
                if e.salary_component in self._manual_earnings:
                    saved = self._manual_earnings[e.salary_component]
                    e.amount = saved['amount']
                    e.is_manual_override = 1
                    if saved.get('default_amount'):
                        e.default_amount = saved['default_amount']
        

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
            if not e.get("default_amount") and e.amount > 0:
                e.default_amount = e.amount
        
        for d in self.deductions:
            if not d.get("default_amount") and d.amount > 0:
                d.default_amount = d.amount

    def recalculate_totals(self):
        """Recalculate totals"""
        saving_percentage = frappe.db.get_value(
            "Salary Structure Assignment",
            {
                "employee": self.employee,
                "docstatus": 1,
                "from_date": ("<=", self.start_date)
            },
            "saving_percentage",
            order_by="from_date desc"
        ) or 0
        
        saving_percentage = flt(saving_percentage)
        self.gross_pay = sum(e.amount for e in self.earnings)
        self.total_deduction = sum(d.amount for d in self.deductions)
        self.net_pay = self.gross_pay - self.total_deduction
        self.total_saving = self.net_pay * (saving_percentage / 100)
        self.total_salary = self.net_pay - self.total_saving
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
        self.payment_days = total_days
        absent_days = sum(1 for a in attendances if a.status == "Absent")
        allowance_deducted_days = sum(1 for a in attendances if a.daily_allowance_deducted)
        payment_days = max(total_days - allowance_deducted_days, 0)

        self.absent_days = absent_days
        self.custom_daily_allowance_deducted_days = allowance_deducted_days

        allowance_rate = frappe.db.get_value("Salary Structure Assignment", self.employee, "tunjangan_harian")
        allowance_rate = flt(allowance_rate)
        allowance_amount = allowance_rate * payment_days

        # Process earnings - SKIP yang manual override
        for e in self.earnings:
            if e.get("is_manual_override") == 1 or e.get("is_manual_override") is True:
                continue

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
            if d.salary_component == "Potongan Zakat":
                continue
            
            if d.get("is_manual_override") == 1 or d.get("is_manual_override") is True:
                continue
            
            if not d.get("default_amount") and d.amount > 0:
                d.default_amount = d.amount


@frappe.whitelist()
def get_attendance_summary(employee, start_date, end_date):
    """Method untuk dipanggil dari client script"""
    start = getdate(start_date)
    end = getdate(end_date)
    
    # Ambil payroll settings
    payroll_settings = frappe.get_cached_value(
        "Payroll Settings",
        None,
        (
            "payroll_based_on",
            "include_holidays_in_total_working_days",
        ),
        as_dict=1,
    )
    
    # Hitung working days (gunakan method dari SalarySlip)
    salary_slip = frappe.get_doc({
        "doctype": "Salary Slip",
        "employee": employee,
        "start_date": start_date,
        "end_date": end_date
    })
    
    working_days = salary_slip.get_payment_days(
        payroll_settings.include_holidays_in_total_working_days
    ) or 0
    
    # Kurangi dengan holiday nasional
    holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
    if not holiday_list:
        company = frappe.db.get_value("Employee", employee, "company")
        holiday_list = frappe.get_cached_value("Company", company, "default_holiday_list")
    
    if holiday_list:
        holidays_data = frappe.db.sql("""
            SELECT 
                holiday_date,
                DAYOFWEEK(holiday_date) as day_of_week,
                weekly_off
            FROM `tabHoliday`
            WHERE parent = %s
            AND holiday_date >= %s
            AND holiday_date <= %s
        """, (holiday_list, start, end), as_dict=1)
        
        national_holidays = [
            h for h in holidays_data 
            if h.weekly_off == 0 and h.day_of_week not in [1, 7]
        ]
        
        working_days = max(working_days - len(national_holidays), 0)
    
    # Ambil attendance
    attendances = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [start, end]],
            "docstatus": 1
        },
        fields=["status", "daily_allowance_deducted"]
    )
    
    total_days = len(attendances)
    absent_days = sum(1 for a in attendances if a.status == "Absent")
    allowance_deducted_days = sum(1 for a in attendances if a.daily_allowance_deducted)
    
    return {
        "absent_days": absent_days,
        "allowance_deducted_days": allowance_deducted_days,
        "payment_days": working_days
    }