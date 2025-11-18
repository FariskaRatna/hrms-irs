# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document
from frappe.utils import getdate, add_days


class BusinessTripAllowance(Document):
	def validate(self):
		if self.business_trip:
			self.calculate_allowance()

	def is_holiday(self, date):
		holiday_list = frappe.db.get_value("Employee", self.employee, "holiday_list")
		if not holiday_list:
			return False

		return frappe.db.exists(
			"Holiday",
			{
				"parent": holiday_list,
				"holiday_date": date
			}
		)

	def calculate_allowance(self):
		departure_date = getdate(self.departure_date)
		return_date = getdate(self.return_date) 
		weekday_count, weekend_count = 0, 0

		date = departure_date
		while date <= return_date:
			if self.is_holiday(date):
				weekend_count += 1
			elif date.weekday() < 5:
				weekday_count += 1
			else:
				weekend_count += 1
			date = add_days(date, 1)

		self.weekend_count = weekend_count
		self.weekday_count = weekday_count

		weekday_info = frappe.db.get_value(
			"Business Trip Allowance Type",
			{
				"position": self.designation,
				"destination": self.destination,
				"day_type": "Weekday"
			},
			["travel_cost", "currency"], as_dict=True
		)

		weekend_info = frappe.db.get_value(
			"Business Trip Allowance Type",
			{
				"position": self.designation,
				"destination": self.destination,
				"day_type": "Weekend"
			},
			["travel_cost", "currency"], as_dict=True
		)

		API_KEY = "YOUR_API_KEY"

		def convert_to_idr(amount, currency):
			if not amount or not currency or currency == "IDR":
				return amount or 0
			
			try:
				url = f"https://api.freecurrencyapi.com/v1/latest?apikey={API_KEY}&currencies=IDR&base_currency={currency}"
				response = requests.get(url)
				if response.status_code == 200:
					data = response.json()
					rate = data["data"]["IDR"]
				else:
					frappe.msgprint(f"Failed to get exchange rate from API ({response.status_code})")
					rate = 1
			except Exception as e:
				frappe.msgprint(f"Error to get exchange rate from API: {e}")
				rate = 1

			return (amount or 0) * rate

		weekday_rate = convert_to_idr(weekday_info.travel_cost if weekday_info else 0, weekday_info.currency if weekday_info else "IDR")
		weekend_rate = convert_to_idr(weekend_info.travel_cost if weekend_info else 0, weekend_info.currency if weekend_info else "IDR")

		total_allowance = (weekday_count * (weekday_rate or 0)) + (weekend_count * (weekend_rate or 0))

		self.allowance_weekday = weekday_rate
		self.allowance_weekend = weekend_rate
		self.total_allowance = total_allowance
