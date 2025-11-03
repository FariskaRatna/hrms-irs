# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class BusinessTrip(Document):
	def before_save(self):
		if self.from_date and self.to_date:
			start = getdate(self.from_date)
			end = getdate(self.to_date)

			days_accumulation = (end - start).days + 1
			self.total_days = days_accumulation

	def on_submit(self):
		if self.status == "Approved":
			self.create_business_trip_allowance()

	def create_business_trip_allowance(self):
		existing_business_trip = frappe.db.exists("Business Trip Allowance", {"business_trip": self.name})
		if existing_business_trip:
			frappe.msgprint("Business Trip Allowance already  exists for this Business Trip")
			return

		bt_doc = frappe.new_doc("Business Trip Allowance")
		bt_doc.employee = self.employee
		bt_doc.business_trip = self.name
		bt_doc.departure_date = self.from_date
		bt_doc.return_date = self.to_date
		bt_doc.total_days = self.total_days
		bt_doc.allowance_amount = 0
		bt_doc.status = "Draft"

		bt_doc.insert(ignore_permissions=True)
		frappe.msgprint(f"Business Trip Allowance {bt_doc.name} created for Employee {self.employee}.")
