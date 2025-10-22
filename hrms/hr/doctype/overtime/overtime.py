# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime


class Overtime(Document):
	def before_save(self):
		if self.start_time and self.end_time:
			fmt = "%H:%M:%S"
			start = datetime.strptime(str(self.start_time), fmt)
			end = datetime.strptime(str(self.end_time), fmt)
			diff = (end - start).seconds / 3600
			self.total_hours = round(diff, 2)
