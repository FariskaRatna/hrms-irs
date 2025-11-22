import frappe
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication

class CustomLeaveApplication(LeaveApplication):

    def on_submit(self):
        # Cek kategori dinas
        if getattr(self, "leave_category", None) == "Dinas":
            frappe.msgprint("Attendance will NOT be created for Dinas.")
            return

        # Jalankan bawaan (update_attendance, ledger, dsb.)
        super().on_submit()
