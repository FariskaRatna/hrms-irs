# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
import pandas as pd
from frappe.utils import getdate

class AttendanceImport(Document):
    pass


@frappe.whitelist()
def process_file(docname):
    doc = frappe.get_doc("Attendance Import", docname)

    if not getattr(doc, "upload_file", None):
        frappe.throw("⚠️ Please upload an Excel file before processing.")

    file_url = doc.upload_file
    if not isinstance(file_url, str):
        frappe.throw("⚠️ Invalid file URL. Please re-upload your file.")

    filename = file_url.split("/")[-1]
    file_path = frappe.utils.get_files_path(filename)

    df = pd.read_excel(file_path)

    required_columns = ["Name", "Date", "Clock In", "Clock Out"]
    for col in required_columns:
        if col not in df.columns:
            frappe.throw(f"Missing column: {col}")

    DEFAULT_LATITUDE = -6,2239100
    DEFAULT_LONGITUDE = 106,8290110

    for _, row in df.iterrows():
        emp = frappe.db.get_value("Employee", {"initial_name": row["Name"]}, "Name")
        if not emp:
            frappe.msgprint(f"⚠️ Employee '{row['Name']}' not found, skipped.")
            continue

        # Pastikan date valid
        try:
            date_part = pd.to_datetime(row["Date"]).date()
        except Exception:
            frappe.msgprint(f"Invalid date for {row['Name']}, skipped")
            continue
        # date_part = pd.to_datetime(row["date"]).date() if pd.notna(row["date"]) else None

        in_time = None
        out_time = None

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
                # time_part = pd.to_datetime(str(row["clock_in"])).time()
                in_time = pd.to_datetime(f"{date_part} {row['Clock In']}")
                # full_datetime = pd.to_datetime(f"{date_part} {time_part}")
                frappe.get_doc({
                    "doctype": "Employee Checkin",
                    "employee": emp,
                    "time": in_time,
                    "log_type": "IN",
                    "latitude": DEFAULT_LATITUDE,
                    "longitude": DEFAULT_LONGITUDE
                }).insert(ignore_permissions=True)
            except Exception as e:
                frappe.msgprint(f"⚠️ Error parsing clock_in for {row['Name']}: {e}")

        # Clock Out
        if pd.notna(row["Clock Out"]) and str(row["Clock Out"]).strip() != "":
            try:
                # time_part = pd.to_datetime(str(row["clock_out"])).time()
                out_time = pd.to_datetime(f"{date_part} {row['Clock Out']}")
                # full_datetime = pd.to_datetime(f"{date_part} {time_part}")
                frappe.get_doc({
                    "doctype": "Employee Checkin",
                    "employee": emp,
                    "time": out_time,
                    "log_type": "OUT",
                    "latitude": DEFAULT_LATITUDE,
                    "longitude", DEFAULT_LONGITUDE
                }).insert(ignore_permissions=True)
            except Exception as e:
                frappe.msgprint(f"⚠️ Error parsing clock_out for {row['Name']}: {e}")

        leave_exists = frappe.db.exists(
            "Leave Application",
            {
                "employee": emp,
                "from_date": ["<=", date_part],
                "to_date": [">=", date_part],
                "docstatus": 1
            }
        )
        
        # if in_time or out_time:
        #     existing_att = frappe.db.exists("Attendance", {
        #         "employee": emp,
        #         "attendance_date": date_part
        #     })

        if in_time and out_time:
            status = "Present"
        elif in_time and not out_time:
            status = "Half Day" if leave_exists else "Absent"
        else:
            status = "Absent"
        
        existing_att = frappe.db.exists("Attendance", {
            "employee": emp,
            "attendance_date": date_part
        })

        if not existing_att:
            att_doc = frappe.get_doc({
                "doctype": "Attendance",
                "employee": emp,
                "attendance_date": date_part,
                "status": "Present",
                "in_time": in_time,
                "out_time": out_time,
                "shift": shift_assignment or None
            })
            att_doc.insert(ignore_permissions=True)
            frappe.msgprint(f"Attendance created for {row['Name']} {date_part}")
        else:
            frappe.msgprint(f"Attendance already exists for {row['Name']} {date_part}")

    frappe.msgprint("✅ Attendance imported successfully!")
