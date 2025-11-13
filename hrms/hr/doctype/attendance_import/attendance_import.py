# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
import pandas as pd
from frappe.utils import getdate
from datetime import date, timedelta
import calendar


class AttendanceImport(Document):
    pass


@frappe.whitelist()
def process_file(docname):
    doc = frappe.get_doc("Attendance Import", docname)

    if not doc.upload_file_finger and not doc.upload_file_face:
        frappe.throw("Please input both file fingerprint and face recognition before processing!")

    def get_file_path(file_url):
        filename = file_url.split("/")[-1]
        file_path = frappe.utils.get_files_path(filename)
        return file_path

    finger_path = get_file_path(doc.upload_file_finger) if doc.upload_file_finger else None
    face_path = get_file_path(doc.upload_file_face) if doc.upload_file_face else None

    df_finger = pd.read_excel(finger_path, dtype=str) if finger_path else pd.DataFrame()
    df_facce = pd.read_excel(face_path, dtype=str) if face_path else pd.DataFrame()

    def parse_data_finger(d):
        try:
            return pd.to_datetime(d, format="%d/%m/%Y", errors="coerce").date()
        except Exception:
            return None

    def parse_data_face(d):
        try:
            return pd.to_datetime(d, format="%d-%m-%Y", errors="coerce").date()
        except Exception:
            return None

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

    # Parsing tanggal
    def parse_date(x):
        try:
            return pd.to_datetime(x, dayfirst=True, errors="coerce")
        except Exception:
            return pd.NaT

    df["Date"] = df["Date"].apply(lambda x: parse_date(str(x).strip()) if pd.notna(x) else pd.NaT)

    # Pastikan kolom wajib ada
    required_columns = ["Name", "Date", "Clock In", "Clock Out"]
    for col in required_columns:
        if col not in df.columns:
            frappe.throw(f"Missing column: {col}")

    # Lokasi default
    DEFAULT_LATITUDE = -6.2239100
    DEFAULT_LONGITUDE = 106.8290110

    # Range tanggal periode (21 s/d 20)
    today = date.today()
    start_day = 21
    start_date = date(today.year, today.month, start_day)
    if today.month == 12:
        end_date = date(today.year + 1, 1, 20)
    else:
        end_date = date(today.year, today.month + 1, 20)

    # Helper: buat checkin jika belum ada
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
            frappe.msgprint(f"⚠️ Skipped duplicate checkin for {emp} at {timestamp}")

    # Loop setiap baris
    for _, row in df.iterrows():
        emp = frappe.db.get_value("Employee", {"initial_name": row["Name"]}, "name")
        if not emp:
            frappe.msgprint(f"⚠️ Employee '{row['Name']}' not found, skipped.")
            continue

        # Pastikan tanggal valid
        try:
            date_part = row["Date"].date()
        except Exception:
            frappe.msgprint(f"⚠️ Invalid date for {row['Name']}, skipped.")
            continue

        in_time, out_time = None, None

        # Ambil shift (kalau ada)
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
        if pd.notna(row["Clock In"]) and str(row["Clock In"]).strip() != "":
            try:
                in_time = pd.to_datetime(f"{date_part} {row['Clock In']}")
                create_checkin_if_not_exists(emp, in_time, "IN")
            except Exception as e:
                frappe.msgprint(f"⚠️ Error parsing Clock In for {row['Name']}: {e}")

        # Clock Out
        if pd.notna(row["Clock Out"]) and str(row["Clock Out"]).strip() != "":
            try:
                out_time = pd.to_datetime(f"{date_part} {row['Clock Out']}")
                create_checkin_if_not_exists(emp, out_time, "OUT")
            except Exception as e:
                frappe.msgprint(f"⚠️ Error parsing Clock Out for {row['Name']}: {e}")

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
            if in_time and out_time:
                status = "Present"
                attendance_reason = "Hadir"
            elif in_time and not out_time:
                status = "Absent"
                attendance_reason = "Tidak Clock Out dan Tanpa Izin"
                daily_allowance_deducted = True
            else:
                status = "Absent"
                attendance_reason = "Tidak Hadir"
                daily_allowance_deducted = True

        # --- Buat Attendance kalau belum ada ---
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
                "in_time": in_time,
                "out_time": out_time,
                "shift": shift_assignment or None,
                "daily_allowance_deducted": daily_allowance_deducted,
                "attendance_reason": attendance_reason,
            })
            att_doc.insert(ignore_permissions=True)
            frappe.msgprint(f"✅ Attendance created for {row['Name']} {date_part}")
        else:
            frappe.msgprint(f"ℹ️ Attendance already exists for {row['Name']} {date_part}")

    frappe.msgprint("🎉 Attendance import completed successfully!")

