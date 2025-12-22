import frappe
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication

class CustomLeaveApplication(LeaveApplication):

    def on_submit(self):
        if getattr(self, "leave_category", None) == "Dinas":
            # frappe.msgprint("Attendance will NOT be created for Dinas.")
            return
        super().on_submit()
    
    def create_attendance(self):
        frappe.logger().info("Attendance creation skipped (custom override)")
        return
    
    def get_title(self):
        return self.purpose or self.name
