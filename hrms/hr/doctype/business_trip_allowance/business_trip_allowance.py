# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days


class BusinessTripAllowance(Document):
	def validate(self):
		if self.business_trip:
			self.calculate_allowance()

	def calculate_allowance(self):
		self.allowance
