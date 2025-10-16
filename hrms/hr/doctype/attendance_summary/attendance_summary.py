# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from datetime import datetime
from frappe.utils import get_first_day, get_last_day


class AttendanceSummary(Document):
	pass

@frappe.whitelist()
def generate_recap(docname):
	doc = frappe.get_doc("Attendance Summary", docname)

	if not doc.month:
		frappe.throw("Please select a month first")

	try:
		year, month = doc.month.split("-")
		year, month = int(year), int(month)
	except:
		frappe.throw("Format of month is wrong. It must be YYYY-MM")

	# month_start = get_first_day(f"{year}-{month}-01").strftime("%Y-%m-%d")
	# month_end = get_last_day(f"{year}-{month}-01").strftime("%Y-%m-%d")
	from datetime import date


	if month == 1:
		start_period = date(year - 1, 12, 21)
	else:
		start_period = date(year, month - 1, 21)
	
	end_period = date(year, month, 20)
	
	frappe.msgprint(f"Start: {start_period}, End: {end_period}")

	# attendances = frappe.get_all(
	# 	"Attendance",
	# 	filters={
	# 		"employee": doc.employee,
	# 		"status": ["in", ["Present", "Late"]],
	# 		"docstatus": 1,
	# 		"attendance_date": ["between", [start_period, end_period]]
	# 	},
	# 	fields=["attendance_date", "in_time", "out_time"]
	# )

	attendances = frappe.get_all(
		"Attendance",
		filters={
			"employee": doc.employee,
			"status": ["in", ["Present", "Late"]],
			"docstatus": 1,
			"attendance_date": ["between", [start_period.strftime("%Y-%m-%d"), end_period.strftime("%Y-%m-%d")]]
		},
		fields=["attendance_date", "in_time", "out_time"]
	)


	frappe.msgprint(f"Attendance ditemukan: {len(attendances)} record")
	for a in attendances:
		frappe.msgprint(str(a.attendance_date))


	day_records = []

	for att in attendances:
		date = att.attendance_date
		checkin = att.in_time
		checkout = att.out_time

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
			shift_start = "08:00:00"
			shift_end = "17:00:00"

		normal_in = datetime.combine(
			getdate(date),
			datetime.strptime(str(shift_start), "%H:%M:%S").time()
		)

		normal_out = datetime.combine(
			getdate(date),
			datetime.strptime(str(shift_end), "%H:%M:%S").time()
		)

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

	over_tolerance = cumulative > threshold

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