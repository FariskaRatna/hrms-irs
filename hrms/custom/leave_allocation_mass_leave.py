import frappe
from frappe.utils import flt
from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation

class CustomLeaveAllocation(LeaveAllocation):

    def create_mass_leave_ledger(self):
        mass_leave_days = self.get_mass_leave_days()

        if mass_leave_days > 0:
            # Buat Leave Ledger Entry NEGATIVE
            frappe.get_doc({
                "doctype": "Leave Ledger Entry",
                "employee": self.employee,
                "leave_type": self.leave_type,
                "transaction_type": "Leave Allocation",
                "transaction_name": self.name,
                "leaves": -mass_leave_days,     # ini yg memotong jatah cuti
                "from_date": self.from_date,
                "to_date": self.to_date,
                "is_carry_forward": 0
            }).insert()

    def get_mass_leave_days(self):
        return frappe.db.get_value("Employee", self.employee, "total_mass_leave") or 0

    def on_submit(self):
        super().on_submit()
        self.create_mass_leave_ledger()
