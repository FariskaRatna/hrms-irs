# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re
from frappe.model.document import Document
import frappe
import pandas as pd
from frappe.utils import getdate, get_datetime
from datetime import date, timedelta, datetime, time
from collections import defaultdict
import calendar
from difflib import get_close_matches
from frappe import _


class AttendanceImport(Document):
    pass


@frappe.whitelist()
def process_file(docname):
    doc = frappe.get_doc("Attendance Import", docname)
    _process_attendance_import(doc)

def _process_attendance_import(doc):
    logs = {
        'success': [],
        'warnings': [],
        'errors': [],
        'skipped': [],
        'stats': {}
    }
    if not doc.upload_file_finger and not doc.upload_file_face:
        frappe.throw("Please input both file fingerprint and face recognition before processing!")
    
    # Range tanggal periode (21 s/d 20)
    today = date.today()
    start_day = 21
    start_date = date(today.year, today.month, start_day)
    if today.month == 12:
        end_date = date(today.year + 1, 1, 20)
    else:
        end_date = date(today.year, today.month + 1, 20)

    def get_file_path(file_url):
        filename = file_url.split("/")[-1]
        file_path = frappe.utils.get_files_path(filename)
        return file_path

    finger_path = get_file_path(doc.upload_file_finger) if doc.upload_file_finger else None
    face_path = get_file_path(doc.upload_file_face) if doc.upload_file_face else None

    df_finger = pd.read_excel(finger_path, dtype=str) if finger_path else pd.DataFrame()
    df_face = pd.read_excel(face_path, dtype=str) if face_path else pd.DataFrame()

    def parse_date_finger(d):
        try:
            return pd.to_datetime(str(d).strip(), format="%d/%m/%Y", errors="coerce")
        except Exception:
            return pd.NaT

    def parse_date_face(d):
        try:
            # return pd.to_datetime(str(d).strip(), format="%Y-%m-%d", errors="coerce")
            return pd.to_datetime(str(d).strip(), errors="coerce").date()
        except Exception:
            return pd.NaT

    def parse_time(y):
        try:
            y = str(y).strip()
            if not y or y.lower() == "nan":
                return None
            if len(y.split(":")) == 2:
                return datetime.strptime(y, "%H:%M").time()
            elif len(y.split(":")) == 3:
                return datetime.strptime(y, "%H:%M:%S").time()
        except Exception:
            return None
        return None  
    
    def find_employee(name, source="finger"):
        if not name:
            return None

        name = str(name).strip()
        field = "initial_name_finger" if source == "finger" else "initial_name_face"
        emp = frappe.db.get_value("Employee", {field: name}, "name")

        if not emp:
            emp = frappe.db.get_value(
                "Employee",
                {field: ["like", f"%{name}%"]},
                "name"
            )
        return emp


    if not df_finger.empty:
        df_finger.rename(columns=lambda x: x.strip(), inplace=True)
        df_finger["Name"] = df_finger["Name"].astype(str).str.strip()
        df_finger["Name"] = df_finger["Name"].str.replace(r"\s+", " ", regex=True)
        required_cols = {"Name", "Date", "Clock In", "Clock Out"}
        if not required_cols.issubset(df_finger.columns):
            frappe.throw("Fingerprint file must contain columns: Name, Date, Clock In, Clock Out")

        # pastikan kolom Date benar-benar jadi object date
        df_finger["Date"] = df_finger["Date"].apply(parse_date_finger)
        df_finger = df_finger[df_finger["Date"].notna()]
        df_finger["Date"] = df_finger["Date"].apply(lambda d: d if isinstance(d, date) else d.date() if pd.notna(d) else None)

        df_finger["Clock In"] = df_finger["Clock In"].apply(parse_time)
        df_finger["Clock Out"] = df_finger["Clock Out"].apply(parse_time)


    if not df_face.empty:
        df_face.rename(columns=lambda x: x.strip(), inplace=True)
        df_face["Name"] = df_face["Name"].astype(str).str.strip()
        df_face["Name"] = df_face["Name"].str.replace(r"\s+", " ", regex=True)
        required_cols = {"Name", "Date", "First-In", "Last-Out"}
        if not required_cols.issubset(df_face.columns):
            frappe.throw("Face recognition file must contain columns: Name, Date, First-In, Last-Out")

        df_face["Date"] = df_face["Date"].apply(parse_date_face)
        df_face = df_face[df_face["Date"].notna()]
        df_face["Date"] = df_face["Date"].apply(lambda d: d if isinstance(d, date) else d.date() if pd.notna(d) else None)


        df_face["First-In"] = df_face["First-In"].apply(parse_time)
        df_face["Last-Out"] = df_face["Last-Out"].apply(parse_time)

    employee_attendance_dates = defaultdict(set)

    for idx, r in df_finger.iterrows():
        emp = find_employee(r["Name"], source="finger")
        if emp and pd.notna(r["Date"]):
            employee_attendance_dates[emp].add(r["Date"])

    for idx, r in df_face.iterrows():
        emp = find_employee(r["Name"], source="face")
        if emp and pd.notna(r["Date"]):
            employee_attendance_dates[emp].add(r["Date"])

    employee_last_date = {
        emp: max(
            d.date() if hasattr(d, "date") else d
            for d in dates
        )
        for emp, dates in employee_attendance_dates.items()
    }


    employees = frappe.db.get_all("Employee", fields=[
        "name",
        "employee_name",
        "initial_name_finger",
        "initial_name_face"
    ])


    DEFAULT_LATITUDE = -6.2239100
    DEFAULT_LONGITUDE = 106.8290110

    created_count = 0
    updated_count = 0
    skipped_count = 0
    weekend_skipped = 0
    duplicate_checkins = 0
    employee_not_found = set()

    def get_existing_checkin_extremes(emp, date_part):
        day_start = datetime.combine(date_part, time.min)
        day_end = datetime.combine(date_part, time.max)

        in_rows = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": emp,
                "log_type": "IN",
                "time": ["between", [day_start, day_end]],
            },
            fields=["time"],
            order_by="time asc",
            limit=1,
        )
        earliest_in = in_rows[0].time if in_rows else None

        out_rows = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": emp,
                "log_type": "OUT",
                "time": ["between", [day_start, day_end]],
            },
            fields=["time"],
            order_by="time desc",
            limit=1,
        )
        latest_out = out_rows[0].time if out_rows else None

        return earliest_in, latest_out
    
    def reconcile_with_existing_checkins(emp, date_part, excel_in_dt, excel_out_dt):
        existing_in, existing_out = get_existing_checkin_extremes(emp, date_part)

        candidates_in = [dt for dt in [excel_in_dt, existing_in] if dt]
        final_in = min(candidates_in) if candidates_in else None

        candidates_out = [dt for dt in [excel_out_dt, existing_out] if dt]
        final_out = max(candidates_out) if candidates_out else None

        if final_in and final_out and final_out <= final_in:
            final_out = None

        # # final IN = paling cepat (min)
        # if excel_in_dt and existing_in:
        #     final_in = excel_in_dt if excel_in_dt <= existing_in else existing_in
        # else:
        #     final_in = excel_in_dt or existing_in

        # # final OUT = paling lama (max)
        # if excel_out_dt and existing_out:
        #     final_out = excel_out_dt if excel_out_dt >= existing_out else existing_out
        # else:
        #     final_out = excel_out_dt or existing_out

        return final_in, final_out

    

    def create_checkin_if_not_exists(emp, timestamp, log_type):
        nonlocal duplicate_checkins

        if not timestamp:
            return

        if timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=frappe.utils.get_time_zone())

        exists = frappe.db.exists("Employee Checkin", {
            "employee": emp,
            "time": timestamp,
            "log_type": log_type
        })
        if not exists:
            doc = frappe.get_doc({
                "doctype": "Employee Checkin",
                "employee": emp,
                "time": timestamp,
                "log_type": log_type,
                "related_dinas_leave": None,
                "latitude": DEFAULT_LATITUDE,
                "longitude": DEFAULT_LONGITUDE,
                "skip_auto_attendance": 0,
                "is_imported": 1
            })
            
            # Set photo ke None dan bypass required validation
            doc.photo = None
            doc.flags.ignore_validate = True
            doc.flags.ignore_mandatory = True

            frappe.flags.ignore_validate = True
            frappe.flags.ignore_permissions = True

            doc.insert()
        else:
            # frappe.msgprint(_("Skipped duplicate checkin for {0} at {1}").format(emp, timestamp))
            duplicate_checkins += 1
    
    created_attendance = set()
    processed_half_day_leaves = {}

    def is_mass_leave(employee, date_part):
        mass_list = frappe.db.get_value("Employee", employee, "mass_leave_list")
        if not mass_list:
            return False

        return frappe.db.exists(
            "Holiday", {
                "parent": mass_list,
                "holiday_date": date_part
            }
        )
    
    def is_holiday(employee, date_part):
        holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
        if not holiday_list:
            return False
        
        return frappe.db.exists(
            "Holiday", {
                "parent": holiday_list,
                "holiday_date": date_part
            }
        )
    
    def att_in_time(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.time()
        if isinstance(value, time):
            return value
        return None
    
    def is_non_working_day(emp, date_part):
        if is_mass_leave(emp, date_part):
            return True
        
        leave = frappe.db.exists(
            "Leave Application",
            {
                "employee": emp,
                "from_date": ["<=", date_part],
                "to_date": [">=", date_part],
                "docstatus": 1
            }
        )
        return bool(leave)
    
    

    for idx, row in df_finger.iterrows():
        # emp = find_employee(row["Name"])
        emp = find_employee(row["Name"], source="finger")
        if not emp:
            employee_not_found.add(row["Name"])
            continue

        try:
            weekday = row["Date"].weekday()
            if weekday in [5, 6]:
                weekend_skipped += 1
                continue
        except Exception:
            pass

        try:
            date_part = row["Date"].date()
        except Exception:
            # frappe.msgprint(_("Invalid date for {0}, skipped.").format(row['Name']))
            logs['errors'].append(f"Invalid date for {row['Name']}")
            continue

        key = (emp, date_part)
        if key in created_attendance:
            # frappe.msgprint(_("Attendance for {0} on {1} already processed, skipped.").format(row['Name'], date_part))
            skipped_count += 1
            continue
        created_attendance.add(key)

        in_time, out_time = row["Clock In"], row["Clock Out"]

        if not df_face.empty:
            emp_face = find_employee(row["Name"], source="face")
            if emp_face:
                emp_face_initial = frappe.db.get_value("Employee", emp_face, "initial_name_face")
                
                if emp_face_initial:
                    face_rows = df_face[df_face["Date"] == date_part]
                    match_row = face_rows[face_rows["Name"] == emp_face_initial]
                    
                    if not match_row.empty:
                        match_row = match_row.iloc[0]
                        face_in_time = match_row["First-In"] if pd.notna(match_row["First-In"]) else None
                        face_out_time = match_row["Last-Out"] if pd.notna(match_row["Last-Out"]) else None
                        
                        # Untuk Clock In: ambil yang paling cepat (earliest)
                        if face_in_time is not None:
                            if in_time is None:
                                in_time = face_in_time
                            else:
                                # Bandingkan dan ambil yang lebih cepat
                                finger_datetime = datetime.combine(date_part, in_time)
                                face_datetime = datetime.combine(date_part, face_in_time)
                                if face_datetime < finger_datetime:
                                    in_time = face_in_time
                        
                        # Untuk Clock Out: ambil yang paling lama (latest)
                        if face_out_time is not None:
                            if out_time is None:
                                out_time = face_out_time
                            else:
                                # Bandingkan dan ambil yang lebih lama
                                finger_datetime = datetime.combine(date_part, out_time)
                                face_datetime = datetime.combine(date_part, face_out_time)
                                if face_datetime > finger_datetime:
                                    out_time = face_out_time

        # if date_part.day == 20 and out_time is None:
        #     out_time = time(18, 0, 0)

        if out_time and in_time and out_time <= in_time:
            # frappe.msgprint(f"⚠️ Out time ({out_time}) lebih awal dari in time ({in_time}) untuk {row['Name']}, di-reset ke None")
            logs['warnings'].append(f"Out time earlier than in time for {row['Name']} on {date_part}")
            out_time = None

        # Baru cek last_date
        last_date = employee_last_date.get(emp)

        # Auto-set out_time jam 18:00 untuk baris terakhir employee
        if (
            last_date
            and date_part == last_date
            and not is_non_working_day(emp, date_part)
        ):
            # frappe.msgprint(f"🔧 Override out_time ke 18:00 untuk {row['Name']} pada {date_part} (last date)")
            out_time = time(18, 0, 0)

        excel_in_datetime = datetime.combine(date_part, in_time) if in_time else None
        excel_out_datetime = datetime.combine(date_part, out_time) if out_time else None

        in_datetime, out_datetime = reconcile_with_existing_checkins(emp, date_part, excel_in_datetime, excel_out_datetime)

        # in_datetime = datetime.combine(date_part, in_time) if in_time else None
        # out_datetime = datetime.combine(date_part, out_time) if out_time else None

        if is_holiday(emp, date_part) and not is_mass_leave(emp, date_part):
            continue

        # Ambil shift
        shift_assignment = frappe.db.get_value(
            "Shift Assignment",
            {
                "employee": emp,
                "start_date": ["<=", date_part],
                "end_date": [">=", date_part]
            },
            "shift_type"
        )

        # Clock In
        # if pd.notna(row["Clock In"]) and str(row["Clock In"]).strip() != "":
        #     try:
        #         in_time = pd.to_datetime(f"{date_part} {row['Clock In']}")
        #         create_checkin_if_not_exists(emp, in_time, "IN")
        #     except Exception as e:
        #         frappe.msgprint(f"⚠️ Error parsing Clock In for {row['Name']}: {e}")

        # # Clock Out
        # if pd.notna(row["Clock Out"]) and str(row["Clock Out"]).strip() != "":
        #     try:
        #         out_time = pd.to_datetime(f"{date_part} {row['Clock Out']}")
        #         create_checkin_if_not_exists(emp, out_time, "OUT")
        #     except Exception as e:
        #         frappe.msgprint(f"⚠️ Error parsing Clock Out for {row['Name']}: {e}")

        # Cek apakah ada cuti/izin/sakit
        leave_exists = frappe.db.exists(
            "Leave Application",
            {
                "employee": emp,
                "from_date": ["<=", date_part],
                "to_date": [">=", date_part],
                "docstatus": 1
            }
        )

        leave_category, doctor_note = None, None
        if leave_exists:
            leave_doc = frappe.get_doc("Leave Application", leave_exists)
            leave_category = getattr(leave_doc, "leave_category", None)
            doctor_note = getattr(leave_doc, "doctor_note", None)

        daily_allowance_deducted = False
        attendance_reason = ""
        status = "Absent"

        # Menentukan Status
        if leave_category:
            if leave_category == "Dinas":
                status = "Present"
                daily_allowance_deducted = False
                attendance_reason = "Hadir"

            if leave_category == "Cuti":
                status = "On Leave"
                daily_allowance_deducted = True
                attendance_reason = "Cuti"

            elif leave_category == "Izin Satu Hari":
                status = "On Leave"
                daily_allowance_deducted = False
                attendance_reason = "Izin"

            elif leave_category == "Sakit":
                if doctor_note:
                    status = "Present"
                    daily_allowance_deducted = False
                    attendance_reason = "Sakit dengan Surat Dokter"
                else:
                    status = "On Leave"
                    daily_allowance_deducted = True
                    attendance_reason = "Sakit tanpa Surat Dokter"

            elif leave_category == "Izin Setengah Hari":
                # att_exists = frappe.db.exists("Attendance", {
                #     "employee": emp,
                #     "attendance_date": date_part
                # })
                valid_half_day_count = frappe.db.count(
                    "Attendance",
                    filters={
                        "employee": emp,
                        "attendance_reason": "Setengah Hari (kurang dari 2 kali)",
                        "attendance_date": ["<", date_part],
                        "docstatus": ["in", [0, 1]]
                    }
                )

                valid_half_day_count += 1

                if valid_half_day_count > 2:
                    status = "Present"
                    daily_allowance_deducted = False
                    attendance_reason = "Setengah Hari (lebih dari 2 kali)"
                else:
                    status = "Present"
                    daily_allowance_deducted = False
                    attendance_reason = "Setengah Hari (kurang dari 2 kali)"

                # if att_exists:
                #     att = frappe.get_doc("Attendance", att_exists)
                #     if att.leave_application:
                #         att.cancel()
                #         att.delete(ignore_permissions=True)
                #         frappe.msgprint(_("Attendance from Izin Setengah Hari override for {0} on {1}").format(row['Name'], date_part))
                #     else:
                #         frappe.msgprint(_("Attendance already exists for {0} on {1}").format(row['Name'], date_part))
                #         continue


        # Cek ada cuti bersama
        elif is_mass_leave(emp, date_part):
            join_date = frappe.db.get_value("Employee", emp, "date_of_joining")
            eligible = False
            if join_date:
                eligible = (date_part - getdate(join_date)).days >= 365

            if eligible: 
                status = "Present"
                daily_allowance_deducted = False
                attendance_reason = "Cuti Bersama"
            else:
                status = "On Leave"
                daily_allowance_deducted = True
                attendance_reason = "Izin"
        
        else:
            if in_datetime and out_datetime:
                status = "Present"
                attendance_reason = "Hadir"
            elif in_datetime and not out_datetime:
                status = "Absent"
                attendance_reason = "Tidak Clock Out dan Tanpa Izin"
                daily_allowance_deducted = True
            else:
                status = "Absent"
                attendance_reason = "Tidak Hadir"
                daily_allowance_deducted = True
        if in_datetime:
            create_checkin_if_not_exists(emp, in_datetime, "IN")
        if out_datetime:
            create_checkin_if_not_exists(emp, out_datetime, "OUT")

        existing_att = frappe.db.exists("Attendance", {
            "employee": emp,
            "attendance_date": date_part
        })

        if not existing_att:
            att_doc = frappe.get_doc({
                "doctype": "Attendance",
                "employee": emp,
                "attendance_date": date_part,
                "status": status,
                "in_time": get_datetime(in_datetime) if in_datetime else None,
                "out_time": get_datetime(out_datetime) if out_datetime else None,
                "shift": shift_assignment or None,
                "daily_allowance_deducted": daily_allowance_deducted,
                "attendance_reason": attendance_reason,
            })
            att_doc.insert(ignore_permissions=True)

            saved = frappe.db.get_value(
                "Attendance",
                att_doc.name,
                ["in_time", "out_time"],
                as_dict=True
            )

            # frappe.msgprint(_("✅ Attendance created for {0} {1}").format(row['Name'], date_part))
            created_count += 1
        else:
            att = frappe.get_doc("Attendance", existing_att)

            if leave_category == "Izin Setengah Hari":
                frappe.db.set_value("Attendance", att.name, {
                    "status": "Present",
                    "attendance_reason": attendance_reason,
                    "daily_allowance_deducted": daily_allowance_deducted,
                    "in_time": get_datetime(in_datetime) if in_datetime else None,
                    "out_time": get_datetime(out_datetime) if out_datetime else None
                    # is_halfday_leave = (leave_category == "Izin Setengah Hari")
                })
                # frappe.msgprint(_("Attendance from Setengah Hari Leave Application for {0} {1}").format(row['Name'], date_part))
                updated_count += 1
                continue
            
            # frappe.msgprint(_("ℹ️ Attendance already exists for {0} {1}").format(row['Name'], date_part))
            updated_count += 1

    logs['stats'] = {
        'fingerprint_rows': len(df_finger),
        'face_rows': len(df_face),
        'created': created_count,
        'updated': updated_count,
        'skipped': skipped_count,
        'weekend_skipped': weekend_skipped,
        'duplicate_checkins': duplicate_checkins,
        'employee_not_found': len(employee_not_found)
    }

    # Build summary message
    summary_html = f"""
    <div style="font-family: monospace;">
        <h3>📊 Attendance Import Summary</h3>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><td><b>Total Fingerprint Rows:</b></td><td>{logs['stats']['fingerprint_rows']}</td></tr>
            <tr><td><b>Total Face Recognition Rows:</b></td><td>{logs['stats']['face_rows']}</td></tr>
            <tr><td><b>✅ Attendance Created:</b></td><td style="color: green;">{logs['stats']['created']}</td></tr>
            <tr><td><b>🔄 Attendance Updated:</b></td><td style="color: blue;">{logs['stats']['updated']}</td></tr>
            <tr><td><b>⏭ Weekend Skipped:</b></td><td>{logs['stats']['weekend_skipped']}</td></tr>
            <tr><td><b>⏩ Duplicate Skipped:</b></td><td>{logs['stats']['skipped']}</td></tr>
            <tr><td><b>🔁 Duplicate Checkins:</b></td><td>{logs['stats']['duplicate_checkins']}</td></tr>
            <tr><td><b>⚠️ Employee Not Found:</b></td><td style="color: orange;">{logs['stats']['employee_not_found']}</td></tr>
        </table>
    """

    # Tambahkan warnings jika ada
    if logs['warnings']:
        summary_html += "<br><h4>⚠️ Warnings:</h4><ul>"
        # Limit to 10 warnings
        for warning in logs['warnings'][:10]:
            summary_html += f"<li>{warning}</li>"
        if len(logs['warnings']) > 10:
            summary_html += f"<li>... and {len(logs['warnings']) - 10} more warnings</li>"
        summary_html += "</ul>"

    # Tambahkan errors jika ada
    if logs['errors']:
        summary_html += "<br><h4>❌ Errors:</h4><ul>"
        for error in logs['errors'][:10]:
            summary_html += f"<li>{error}</li>"
        if len(logs['errors']) > 10:
            summary_html += f"<li>... and {len(logs['errors']) - 10} more errors</li>"
        summary_html += "</ul>"

    # Tambahkan employee not found jika ada
    if employee_not_found:
        summary_html += "<br><h4>👤 Employee Not Found:</h4><ul>"
        for emp_name in list(employee_not_found)[:10]:
            summary_html += f"<li>{emp_name}</li>"
        if len(employee_not_found) > 10:
            summary_html += f"<li>... and {len(employee_not_found) - 10} more</li>"
        summary_html += "</ul>"

    summary_html += "</div>"

    # Tampilkan SATU kali saja di akhir
    frappe.msgprint(
        summary_html,
        title="Attendance Import Completed",
        indicator="green",
        wide=True
    )


