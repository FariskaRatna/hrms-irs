import frappe
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication

class CustomLeaveApplication(LeaveApplication):

    def on_submit(self):
        frappe.enqueue(
            "hrms.custom.dinas_and_setengah_hari_sync.sync_for_leave",
            leave_name=self.name,
            queue="long"
        )

    # def on_submit(self):
    #     if getattr(self, "leave_category", None) == "Dinas":
    #         # frappe.msgprint("Attendance will NOT be created for Dinas.")
    #         return
    #     super().on_submit()
    
    # def create_attendance(self):
    #     frappe.logger().info("Attendance creation skipped")
    #     return
    
    # def get_title(self):
    #     return self.purpose or self.name
