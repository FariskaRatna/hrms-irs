# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_datetime, getdate, add_months, nowdate, formatdate

from hrms.hr.doctype.shift_assignment.shift_assignment import get_actual_start_end_datetime_of_shift
from hrms.hr.utils import (
	get_distance_between_coordinates,
	set_geolocation_from_coordinates,
	validate_active_employee,
)


class CheckinRadiusExceededError(frappe.ValidationError):
	pass


class EmployeeCheckin(Document):
	def before_validate(self):
		self.time = get_datetime(self.time).replace(microsecond=0)

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_duplicate_log()
		self.validate_time_change()
		self.fetch_shift()
		self.set_geolocation()
		self.validate_distance_from_shift_location()
		self.validate_after_choose_dinas()
		# self.validate_dinas_permission()

	def validate_after_choose_dinas(self):
		if getattr(self, "is_imported", 0):
			return

		if not self.related_dinas_leave:
			frappe.throw("Please choose Leave Application  for Dinas first.")

		two_months_ago = getdate(add_months(nowdate(), -4))
		leave = frappe.get_doc("Leave Application", self.related_dinas_leave)

		if getdate(leave.modified) < two_months_ago:
			frappe.throw("This Leave Application is more than 2 months ago and do not valid for employee checkin.")

		checkin_date = getdate(self.time)
		from_date = getdate(leave.from_date)
		to_date = getdate(leave.to_date)

		if not (from_date <= checkin_date <= to_date):
			frappe.throw(
				f"Checkin Date ({formatdate(checkin_date)}) should be on the range "
				f"Leave Dinas: {formatdate(from_date)} → {formatdate(to_date)}."
			)

	# employee don't have access to create employee checkin without leave application before

	# def validate_dinas_permission(self):
	# 	check_date = getdate(self.time)

	# 	if not self.flags.in_import and not self.flags.in_bulk_insert:
	# 		dinas_leave = frappe.db.exists(
	# 			"Leave Application",
	# 			{
	# 				"employee": self.employee,
	# 				"from_date": ["<=", check_date],
	# 				"to_date": [">=", check_date],
	# 				"leave_category": "Dinas",
	# 				# "status": "Approved"
	# 				"status": ["not in", ["Rejected", "Cancelled"]],
	# 			}
	# 		)

	# 		if not dinas_leave:
	# 			frappe.throw(
	# 				"You don't have active Dinas Leave for this date. You cannot create an employee checkin."
	# 			)

	def validate_duplicate_log(self):
		doc = frappe.db.exists(
			"Employee Checkin",
			{
				"employee": self.employee,
				"time": self.time,
				"name": ("!=", self.name),
				"log_type": self.log_type,
			},
		)
		if doc:
			doc_link = frappe.get_desk_link("Employee Checkin", doc)
			frappe.throw(
				_("This employee already has a log with the same timestamp.{0}").format("<Br>" + doc_link)
			)

	def validate_time_change(self):
		if self.attendance and self.has_value_changed("time"):
			frappe.throw(
				title=_("Cannot Modify Time"),
				msg=_(
					"An attendance record is linked to this checkin. Please cancel the attendance before modifying time."
				),
			)

	@frappe.whitelist()
	def set_geolocation(self):
		set_geolocation_from_coordinates(self)

	@frappe.whitelist()
	def fetch_shift(self):
		if not (
			shift_actual_timings := get_actual_start_end_datetime_of_shift(
				self.employee, get_datetime(self.time), True
			)
		):
			self.shift = None
			self.offshift = 1
			return

		if (
			shift_actual_timings.shift_type.determine_check_in_and_check_out
			== "Strictly based on Log Type in Employee Checkin"
			and not self.log_type
			and not self.skip_auto_attendance
		):
			frappe.throw(
				_("Log Type is required for check-ins falling in the shift: {0}.").format(
					shift_actual_timings.shift_type.name
				)
			)
		if not self.attendance:
			self.offshift = 0
			self.shift = shift_actual_timings.shift_type.name
			self.shift_actual_start = shift_actual_timings.actual_start
			self.shift_actual_end = shift_actual_timings.actual_end
			self.shift_start = shift_actual_timings.start_datetime
			self.shift_end = shift_actual_timings.end_datetime

	def validate_distance_from_shift_location(self):
		if not frappe.db.get_single_value("HR Settings", "allow_geolocation_tracking"):
			return

		if not (self.latitude or self.longitude):
			frappe.throw(_("Latitude and longitude values are required for checking in."))

		assignment_locations = frappe.get_all(
			"Shift Assignment",
			filters={
				"employee": self.employee,
				"shift_type": self.shift,
				"start_date": ["<=", self.time],
				"shift_location": ["is", "set"],
				"docstatus": 1,
				"status": "Active",
			},
			or_filters=[["end_date", ">=", self.time], ["end_date", "is", "not set"]],
			pluck="shift_location",
		)
		if not assignment_locations:
			return

		checkin_radius, latitude, longitude = frappe.db.get_value(
			"Shift Location", assignment_locations[0], ["checkin_radius", "latitude", "longitude"]
		)
		if checkin_radius <= 0:
			return

		distance = get_distance_between_coordinates(latitude, longitude, self.latitude, self.longitude)
		if distance > checkin_radius:
			frappe.throw(
				_("You must be within {0} meters of your shift location to check in.").format(checkin_radius),
				exc=CheckinRadiusExceededError,
			)


@frappe.whitelist()
def add_log_based_on_employee_field(
	employee_field_value,
	timestamp,
	device_id=None,
	log_type=None,
	skip_auto_attendance=0,
	employee_fieldname="attendance_device_id",
	latitude=None,
	longitude=None,
):
	"""Finds the relevant Employee using the employee field value and creates a Employee Checkin.

	:param employee_field_value: The value to look for in employee field.
	:param timestamp: The timestamp of the Log. Currently expected in the following format as string: '2019-05-08 10:48:08.000000'
	:param device_id: (optional)Location / Device ID. A short string is expected.
	:param log_type: (optional)Direction of the Punch if available (IN/OUT).
	:param skip_auto_attendance: (optional)Skip auto attendance field will be set for this log(0/1).
	:param employee_fieldname: (Default: attendance_device_id)Name of the field in Employee DocType based on which employee lookup will happen.
	:latitude: (optional) Latitude of the shift location.
	:longitude: (optional) Longitude of the shift location.
	"""

	if not employee_field_value or not timestamp:
		frappe.throw(_("'employee_field_value' and 'timestamp' are required."))

	employee = frappe.db.get_values(
		"Employee",
		{employee_fieldname: employee_field_value},
		["name", "employee_name", employee_fieldname],
		as_dict=True,
	)
	if employee:
		employee = employee[0]
	else:
		frappe.throw(
			_("No Employee found for the given employee field value. '{}': {}").format(
				employee_fieldname, employee_field_value
			)
		)

	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee.name
	doc.employee_name = employee.employee_name
	doc.time = timestamp
	doc.device_id = device_id
	doc.log_type = log_type
	doc.latitude = latitude
	doc.longitude = longitude
	if cint(skip_auto_attendance) == 1:
		doc.skip_auto_attendance = "1"
	doc.insert()

	return doc


@frappe.whitelist()
def bulk_fetch_shift(checkins: list[str] | str) -> None:
	if isinstance(checkins, str):
		checkins = frappe.json.loads(checkins)
	for d in checkins:
		doc = frappe.get_doc("Employee Checkin", d)
		doc.fetch_shift()
		doc.flags.ignore_validate = True
		doc.save()


def mark_attendance_and_link_log(
	logs,
	attendance_status,
	attendance_date,
	working_hours=None,
	late_entry=False,
	early_exit=False,
	in_time=None,
	out_time=None,
	shift=None,
):
	"""Creates an attendance and links the attendance to the Employee Checkin.
	Note: If attendance is already present for the given date, the logs are marked as skipped and no exception is thrown.

	:param logs: The List of 'Employee Checkin'.
	:param attendance_status: Attendance status to be marked. One of: (Present, Absent, Half Day, Skip). Note: 'On Leave' is not supported by this function.
	:param attendance_date: Date of the attendance to be created.
	:param working_hours: (optional)Number of working hours for the given date.
	"""
	log_names = [x.name for x in logs]
	employee = logs[0].employee

	if attendance_status == "Skip":
		skip_attendance_in_checkins(log_names)
		return None

	elif attendance_status in ("Present", "Absent", "Half Day"):
		try:
			frappe.db.savepoint("attendance_creation")
			if attendance := get_existing_half_day_attendance(employee, attendance_date):
				frappe.db.set_value(
					"Attendance",
					attendance.name,
					{
						"working_hours": working_hours,
						"shift": shift,
						"late_entry": late_entry,
						"early_exit": early_exit,
						"in_time": in_time,
						"out_time": out_time,
						"half_day_status": "Absent" if attendance_status == "Absent" else "Present",
						"modify_half_day_status": 0,
					},
				)
			else:
				attendance = frappe.new_doc("Attendance")
				attendance.update(
					{
						"doctype": "Attendance",
						"employee": employee,
						"attendance_date": attendance_date,
						"status": attendance_status,
						"working_hours": working_hours,
						"shift": shift,
						"late_entry": late_entry,
						"early_exit": early_exit,
						"in_time": in_time,
						"out_time": out_time,
						"half_day_status": "Absent" if attendance_status == "Half Day" else None,
					}
				).submit()

			if attendance_status == "Absent":
				attendance.add_comment(
					text=_("Employee was marked Absent for not meeting the working hours threshold.")
				)

			update_attendance_in_checkins(log_names, attendance.name)
			return attendance

		except frappe.ValidationError as e:
			handle_attendance_exception(log_names, e)

	else:
		frappe.throw(_("{} is an invalid Attendance Status.").format(attendance_status))


def get_existing_half_day_attendance(employee, attendance_date):
	attendance_name = frappe.db.exists(
		"Attendance",
		{
			"employee": employee,
			"attendance_date": attendance_date,
			"status": "Half Day",
			"modify_half_day_status": 1,
			"leave_type": ("is", "set"),
		},
	)

	if attendance_name:
		attendance_doc = frappe.get_doc("Attendance", attendance_name)
		return attendance_doc
	return None


def calculate_working_hours(logs, check_in_out_type, working_hours_calc_type):
	"""Given a set of logs in chronological order calculates the total working hours based on the parameters.
	Zero is returned for all invalid cases.

	:param logs: The List of 'Employee Checkin'.
	:param check_in_out_type: One of: 'Alternating entries as IN and OUT during the same shift', 'Strictly based on Log Type in Employee Checkin'
	:param working_hours_calc_type: One of: 'First Check-in and Last Check-out', 'Every Valid Check-in and Check-out'
	"""
	total_hours = 0
	in_time = out_time = None
	if check_in_out_type == "Alternating entries as IN and OUT during the same shift":
		in_time = logs[0].time
		if len(logs) >= 2:
			out_time = logs[-1].time
		if working_hours_calc_type == "First Check-in and Last Check-out":
			# assumption in this case: First log always taken as IN, Last log always taken as OUT
			total_hours = time_diff_in_hours(in_time, logs[-1].time)
		elif working_hours_calc_type == "Every Valid Check-in and Check-out":
			logs = logs[:]
			while len(logs) >= 2:
				total_hours += time_diff_in_hours(logs[0].time, logs[1].time)
				del logs[:2]

	elif check_in_out_type == "Strictly based on Log Type in Employee Checkin":
		if working_hours_calc_type == "First Check-in and Last Check-out":
			first_in_log_index = find_index_in_dict(logs, "log_type", "IN")
			first_in_log = logs[first_in_log_index] if first_in_log_index or first_in_log_index == 0 else None
			last_out_log_index = find_index_in_dict(reversed(logs), "log_type", "OUT")
			last_out_log = (
				logs[len(logs) - 1 - last_out_log_index]
				if last_out_log_index or last_out_log_index == 0
				else None
			)
			in_time = getattr(first_in_log, "time", None)
			out_time = getattr(last_out_log, "time", None)
			if first_in_log and last_out_log:
				total_hours = time_diff_in_hours(in_time, out_time)
		elif working_hours_calc_type == "Every Valid Check-in and Check-out":
			in_log = out_log = None
			for log in logs:
				if in_log and out_log:
					if not in_time:
						in_time = in_log.time
					out_time = out_log.time
					total_hours += time_diff_in_hours(in_log.time, out_log.time)
					in_log = out_log = None
				if not in_log:
					in_log = log if log.log_type == "IN" else None
					if in_log and not in_time:
						in_time = in_log.time
				elif not out_log:
					out_log = log if log.log_type == "OUT" else None

			if in_log and out_log:
				out_time = out_log.time
				total_hours += time_diff_in_hours(in_log.time, out_log.time)

	return total_hours, in_time, out_time


def time_diff_in_hours(start, end):
	return round(float((end - start).total_seconds()) / 3600, 2)


def find_index_in_dict(dict_list, key, value):
	return next((index for (index, d) in enumerate(dict_list) if d[key] == value), None)


def handle_attendance_exception(log_names: list, error_message: str):
	frappe.db.rollback(save_point="attendance_creation")
	frappe.clear_messages()
	skip_attendance_in_checkins(log_names)
	add_comment_in_checkins(log_names, error_message)


def add_comment_in_checkins(log_names: list, error_message: str):
	text = "{prefix}<br>{error_message}".format(
		prefix=frappe.bold(_("Reason for skipping auto attendance:")), error_message=error_message
	)

	for name in log_names:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "Employee Checkin",
				"reference_name": name,
				"content": text,
			}
		).insert(ignore_permissions=True)


def skip_attendance_in_checkins(log_names: list):
	EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
	(
		frappe.qb.update(EmployeeCheckin)
		.set("skip_auto_attendance", 1)
		.where(EmployeeCheckin.name.isin(log_names))
	).run()


def update_attendance_in_checkins(log_names: list, attendance_id: str):
	EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
	(
		frappe.qb.update(EmployeeCheckin)
		.set("attendance", attendance_id)
		.where(EmployeeCheckin.name.isin(log_names))
	).run()

# def update_attendance_from_checkin(doc, method):
# 	employee = doc.employee
# 	log_date = getdate(doc.time)

# 	attendance_name = frappe.db.exists("Attendance", {
# 		"employee": employee,
# 		"attendance_date": log_date
# 	})

# 	if not attendance_name:
# 		attendance_doc = frappe.new_doc("Attendance")
# 		attendance_doc.employee = employee
# 		attendance_doc.attendance_date = log_date
# 		attendance_doc.status = "Present"
# 		attendance_doc.save(ignore_permissions=True)
# 		frappe.db.commit()
# 	else:
# 		attendance_doc = frappe.get_doc("Attendance", attendance_name)
# 		if attendance_doc.status != "Present":
# 			attendance_doc.status = "Present"
# 			attendance_doc.save(ignore_permissions=True)
# 			frappe.db.commit()

# def after_insert(doc, method=None):
# 	update_attendance_from_checkin(doc, method)

@frappe.whitelist()
def sync_unlinked_attendances():
	import frappe
	from frappe.utils import getdate
	from hrms.hr.doctype.employee_checkin.employee_checkin import mark_attendance_and_link_log

	frappe.flags.ignore_dinas_block = True
	frappe.flags.force_sync_present = True

	checkins = frappe.get_all(
		"Employee Checkin",
		filters={"attendance": ["is", "not set"], "docstatus": ["in", [0, 1]]},
		fields=["name", "employee", "time", "docstatus"]
	)

	if not checkins:
		return "All check-ins have been linked to Attendance."

	grouped = {}

	for chk in checkins:
		date = getdate(chk["time"])
		key = f"{chk['employee']}_{date}"

		if key not in grouped:
			grouped[key] = {
				"employee": chk["employee"],
				"date": date,
				"times": [],
				"records": []
			}

		grouped[key]["times"].append(chk["time"])
		grouped[key]["records"].append(chk["name"])
		

	created, skipped = 0, 0

	for key, data in grouped.items():
		employee = data["employee"]
		date = data["date"]
		times = sorted(data["times"])

		existing_att = frappe.db.exists("Attendance", {"employee": employee, "attendance_date": date})

		if existing_att:
			skipped += 1
			continue

		att = frappe.new_doc("Attendance")
		att.employee = employee
		att.attendance_date = date
		att.status = "Present"
		att.company = frappe.db.get_value("Employee", employee, "company")

		att.check_in = times[0]
		att.check_out = times[-1]

		att.insert(ignore_permissions=True)
		att.submit()

		for chk in data["records"]:
			frappe.db.set_value("Employee Checkin", chk, "attendance", att.name)

		created += 1

	frappe.flags.force_sync_present = False
	frappe.db.commit()


	return f"{created} Attendance has successfully created."


# Filter for choose leave application dinas for 2 months back
# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_recent_dinas_leaves(doctype, txt, searchfield, start, page_len, filters):
#     employee = filters.get("employee")

#     if not employee:
#         return []

#     from datetime import datetime
#     from dateutil.relativedelta import relativedelta

#     # tanggal hari ini - 4 bulan
#     min_date = (datetime.today() - relativedelta(months=5)).date()

#     return frappe.db.sql("""
#         SELECT name, leave_type, from_date, to_date
#         FROM `tabLeave Application`
#         WHERE employee = %s
#         AND leave_category = 'Dinas'
#         AND from_date >= %s
#         ORDER BY from_date DESC
#         LIMIT %s OFFSET %s
#     """, (employee, min_date, page_len, start))
