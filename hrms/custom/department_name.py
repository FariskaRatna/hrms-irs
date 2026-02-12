import frappe
from erpnext.setup.doctype.department.department import Department

class CustomDepartment(Department):
    def autoname(self):
        self.name = self.department_name