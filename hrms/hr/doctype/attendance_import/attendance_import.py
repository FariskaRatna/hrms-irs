# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
import pandas as pd
from frappe.utils import getdate
from datetime import date, timedelta, datetime
import calendar
from difflib import get_close_matches


class AttendanceImport(Document):
    pass


@frappe.whitelist()
def process_file(docname):
    doc = frappe.get_doc("Attendance Import", docname)

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
            return pd.to_datetime(str(d).strip(), format="%Y-%m-%d", errors="coerce")
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

    if not df_finger.empty:
        df_finger.rename(columns=lambda x: x.strip(), inplace=True)
        required_cols = {"Name", "Date", "Clock In", "Clock Out"}
        if not required_cols.issubset(df_finger.columns):
            frappe.throw("Fingerprint file must contain columns: Name, Date, Clock In, Clock Out")

        # pastikan kolom Date benar-benar jadi object date
        df_finger["Date"] = df_finger["Date"].apply(parse_date_finger)
        df_finger = df_finger[df_finger["Date"].notna()]
        df_finger["Date"] = df_finger["Date"].apply(lambda d: d if isinstance(d, date) else d.date() if pd.notna(d) else None)
        df_finger = df_finger.astype({"Date": "object"})  # penting: hindari dtype datetime64
        
        # df_finger = df_finger[
        #     (df_finger["Date"] >= start_date) & (df_finger["Date"] <= end_date)
        # ]
        df_finger["Clock In"] = df_finger["Clock In"].apply(parse_time)
        df_finger["Clock Out"] = df_finger["Clock Out"].apply(parse_time)


    if not df_face.empty:
        df_face.rename(columns=lambda x: x.strip(), inplace=True)
        required_cols = {"Name", "Date", "First-In", "Last-Out"}
        if not required_cols.issubset(df_face.columns):
            frappe.throw("Face recognition file must contain columns: Name, Date, First-In, Last-Out")

        df_face["Date"] = df_face["Date"].apply(parse_date_face)
        df_face = df_face[df_face["Date"].notna()]
        df_face["Date"] = df_face["Date"].apply(lambda d: d if isinstance(d, date) else d.date() if pd.notna(d) else None)
        df_face = df_face.astype({"Date": "object"})  # hindari dtype datetime64

        # df_face = df_face[
        #     (df_face["Date"] >= start_date) & (df_face["Date"] <= end_date)
        # ]
        df_face["First-In"] = df_face["First-In"].apply(parse_time)
        df_face["Last-Out"] = df_face["Last-Out"].apply(parse_time)


    employees = frappe.db.get_all("Employee", fields=["name", "employee_name", "initial_name"])
    employee_names = [e.employee_name for e in employees] + [e.initial_name for e in employees if e.initial_name]

    def find_employee(name):
        matches = get_close_matches(str(name).strip(), employee_names, n=1, cutoff=0.8)
        if matches:
            emp = next((e for e in employees if e.employee_name == matches[0] or e.initial_name == matches[0]), None)
            return emp.name if emp else None
        return None

    DEFAULT_LATITUDE = -6.2239100
    DEFAULT_LONGITUDE = 106.8290110

    def create_checkin_if_not_exists(emp, timestamp, log_type):
        exists = frappe.db.exists("Employee Checkin", {
            "employee": emp,
            "time": timestamp,
            "log_type": log_type
        })
        if not exists:
            frappe.get_doc({
                "doctype": "Employee Checkin",
                "employee": emp,
                "time": timestamp,
                "log_type": log_type,
                "latitude": DEFAULT_LATITUDE,
                "longitude": DEFAULT_LONGITUDE
            }).insert(ignore_permissions=True)
        else:
            frappe.msgprint(f"Skipped duplicate checkin for {emp} at {timestamp}")
    
    created_attendance = set()

    for _, row in df_finger.iterrows():
        emp = find_employee(row["Name"])
        if not emp:
            frappe.msgprint(f"Employee '{row['Name']}' not found, skipped.")
            continue

        try:
            weekday = row["Date"].weekday()
            if weekday in [5, 6]:
                frappe.msgprint(f"⛔ Skipped weekend for {row['Name']} on {row['Date']}")
                continue
        except Exception:
            pass

        try:
            date_part = row["Date"].date()
        except Exception:
            frappe.msgprint(f"Invalid date for {row['Name']}, skipped.")
            continue
        key = (emp, date_part)
        if key in created_attendance:
            frappe.msgprint(f"Attendance for {row['Name']} on {date_part} already processed, skipped.")
            continue
        created_attendance.add(key)

        in_time, out_time = row["Clock In"], row["Clock Out"]

        if (not in_time or not out_time) and not df_face.empty:
            face_row = df_face[(df_face["Date"] == date_part)]
            if not face_row.empty:
                candidates = face_row["Name"].tolist()
                matched = get_close_matches(row["Name"], candidates, n=1, cutoff=0.8)
                if matched:
                    match_row = face_row[face_row["Name"] == matched[0]].iloc[0]
                    if not in_time and pd.notna(match_row["First-In"]):
                        in_time = match_row["First-In"]
                        frappe.msgprint(f"Filled missing Clock In for {row['Name']} from Face data")
                    if not out_time and pd.notna(match_row["Last-Out"]):
                        out_time = match_row["Last-Out"]
                        frappe.msgprint(f"Filled missing Clock Out for {row['Name']} from Face data")
            
        in_datetime = datetime.combine(date_part, in_time) if in_time else None
        out_datetime = datetime.combine(date_part, out_time) if out_time else None

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

        # --- Tentukan status ---
        if leave_category:
            if leave_category == "Cuti":
                status = "On Leave"
                daily_allowance_deducted = True
                attendance_reason = "Cuti"

            elif leave_category == "Izin":
                status = "On Leave"
                daily_allowance_deducted = True
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

            elif leave_category == "Setengah Hari":
                half_day_count = frappe.db.count(
                    "Leave Application",
                    filters={
                        "employee": emp,
                        "leave_category": "Setengah Hari",
                        "from_date": ["between", [start_date, end_date]],
                        "docstatus": 1
                    }
                )
                if half_day_count <= 2:
                    status = "Present"
                    daily_allowance_deducted = False
                    attendance_reason = "Setengah Hari (kurang dari 2 kali)"
                else:
                    status = "On Leave"
                    daily_allowance_deducted = True
                    attendance_reason = "Setengah Hari (lebih dari 2 kali)"
        else:
            # Tidak ada leave, tentukan berdasarkan clock-in/out
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

        # Buat Attendance kalau belum ada
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
                "in_time": in_datetime,
                "out_time": out_datetime,
                "shift": shift_assignment or None,
                "daily_allowance_deducted": daily_allowance_deducted,
                "attendance_reason": attendance_reason,
            })
            att_doc.insert(ignore_permissions=True)
            frappe.msgprint(f"✅ Attendance created for {row['Name']} {date_part}")
        else:
            frappe.msgprint(f"ℹ️ Attendance already exists for {row['Name']} {date_part}")

    frappe.msgprint("Attendance import completed successfully!")

    frappe.msgprint(f"Total Fingerprint Rows: {len(df_finger)}")
    frappe.msgprint(f"Total Face Rows: {len(df_face)}")
    frappe.msgprint(f"Total Attendance Created: {len(created_attendance)}")


