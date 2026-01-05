# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from datetime import datetime
from frappe.utils import get_first_day, get_last_day, date_diff, cint, add_days

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from hrms.utils.holiday_list import get_holiday_dates_between

HOLIDAYS_BETWEEN_DATES = "holiday_between_dates"

class AttendanceSummary(Document):
	pass

@frappe.whitelist()
def generate_recap(docname):
	doc = frappe.get_doc("Attendance Summary", docname)

	start_period = doc.from_date
	end_period = doc.to_date

	attendances = frappe.get_all(
		"Attendance",
		filters={
			"employee": doc.employee,
			"status": ["in", ["Present", "Late"]],
			"docstatus": 1,
			"attendance_date": ["between", [start_period.strftime("%Y-%m-%d"), end_period.strftime("%Y-%m-%d")]]
		},
		fields=["attendance_date", "in_time", "out_time", "attendance_reason"]
	)

	working_days = date_diff(end_period, start_period) + 1
	holidays = get_holidays_for_employee(doc.employee, start_period, end_period)
	working_days_list = [add_days(getdate(start_period), days=day) for day in range(0, working_days)]

	working_days_list = [i for i in working_days_list if i not in holidays]

	working_days -= len(holidays)

	absent, present = calculate_absent_present(doc.employee, start_period, end_period)
	doc.total_absent = absent
	doc.total_present = present


	frappe.msgprint(f"Attendance ditemukan: {len(attendances)} record")
	for a in attendances:
		frappe.msgprint(str(a.attendance_date))


	day_records = []

	for att in attendances:
		date = att.attendance_date
		checkin = att.in_time
		checkout = att.out_time

		reason = att.attendance_reason or ""

		if reason in [
			"Setengah Hari (kurang dari 2 kali)",
			"Setengah Hari (waktu tidak sesuai)"
		]:
			continue

		if not (checkin and checkout):
			continue
		
		checkin = datetime.strptime(str(checkin), "%Y-%m-%d %H:%M:%S")
		checkout = datetime.strptime(str(checkout), "%Y-%m-%d %H:%M:%S")
		
		shift_assignment = frappe.db.get_value(
			"Shift Assignment",
			{
				"employee": doc.employee,
				"start_date": ["<=", date],
				"end_date": [">=", date]
			},
			"shift_type"
		)

		if shift_assignment:
			shift_start, shift_end = frappe.db.get_value(
				"Shift Type",
				shift_assignment,
				["start_time", "end_time"]
			)
		else:
			shift_start = "09:15:00"
			shift_end = "18:00:00"

		normal_in = datetime.combine(
			getdate(date),
			datetime.strptime(str(shift_start), "%H:%M:%S").time()
		)

		normal_out = datetime.combine(
			getdate(date),
			datetime.strptime(str(shift_end), "%H:%M:%S").time()
		)

		late_in = 0
		early_out = 0

		if checkin > normal_in:
			late_in = (checkin - normal_in).seconds // 60
			if late_in > 0:
				day_records.append((late_in, f"{date} (IN)"))

		if checkout < normal_out:
			early_out = (normal_out - checkout).seconds // 60
			if early_out > 0:
				day_records.append((early_out, f"{date} (OUT)"))
		
		# total_day = late_in + early_out

		# if total_day > 0:
		# 	day_records.append((total_day, date))
	
	day_records.sort(key=lambda x: x[0])

	doc.set("late_details", [])

	cumulative = 0
	total_late_minutes = 0
	late_days = 0
	late_dates = []
	threshold = 180	

	for total_day, date in day_records:
		cumulative += total_day
		total_late_minutes += total_day

		if cumulative > threshold:
			late_days += 1
			late_dates.append(date)

			row = doc.append("late_details", {})
			raw_date, log_type = date.split(" ")

			row.date = raw_date
			row.log_type = log_type.strip("()")
			row.minutes = total_day


	over_tolerance = cumulative > threshold

	doc.total_working_days = working_days
	doc.total_late_minutes = total_late_minutes
	doc.late_days = late_days
	doc.over_tolerance = 1 if over_tolerance else 0
	doc.late_dates = "\n".join(late_dates)
	doc.last_updated_on = frappe.utils.now()
	doc.remarks = (
		"Melebihi toleransi keterlambatan (180 menit)"
		if over_tolerance
		else 'Masih dalam batas toleransi'
	)

	doc.save()

	frappe.msgprint(f"Recap for {doc.employee_name} - {doc.month} generated")


def get_holidays_for_employee(employee, start_date, end_date):
	holiday_list = get_holiday_list_for_employee(employee)
	key = f"{holiday_list}:{start_date}:{end_date}"
	holiday_dates = frappe.cache().hget(HOLIDAYS_BETWEEN_DATES, key)

	if not holiday_dates:
		holiday_dates = get_holiday_dates_between(holiday_list, start_date, end_date)
		frappe.cache().hset(HOLIDAYS_BETWEEN_DATES, key, holiday_dates)

	return holiday_dates

def calculate_absent_present(employee, start_date, end_date):
	absent = 0
	present = 0

	attendance_details = frappe.get_all(
		"Attendance",
		filters={"employee": employee, "attendance_date": ["between", [start_date, end_date]]},
		fields=["status", "attendance_reason"]
	)

	for d in attendance_details:
		if d.status == "Absent":
			absent += 1

		elif d.status == "Present":
			present += 1
		
		elif d.status == "On Leave" and d.attendance_reason in ["Sakit dengan Surat Dokter", "Cuti", "Cuti Bersama"]:
			present += 1

		elif d.status == "On Leave" and d.attendance_reason == "Izin":
			absent += 1

	return absent, present
