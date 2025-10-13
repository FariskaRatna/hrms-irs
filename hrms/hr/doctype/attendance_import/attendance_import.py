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

    required_columns = ["name", "date", "clock_in", "clock_out"]
    for col in required_columns:
        if col not in df.columns:
            frappe.throw(f"Missing column: {col}")

    for _, row in df.iterrows():
        emp = frappe.db.get_value("Employee", {"initial_name": row["name"]}, "name")
        if not emp:
            frappe.msgprint(f"⚠️ Employee '{row['name']}' not found, skipped.")
            continue

        # Pastikan date valid
        try:
            date_part = pd.to_datetime(row["date"]).date()
        except Exception:
            frappe.msgprint(f"Invalid date for {row['name']}, skipped")
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
        if pd.notna(row["clock_in"]) and str(row["clock_in"]).strip() != "":
            try:
                # time_part = pd.to_datetime(str(row["clock_in"])).time()
                in_time = pd.to_datetime(f"{date_part} {row['clock_in']}")
                # full_datetime = pd.to_datetime(f"{date_part} {time_part}")
                frappe.get_doc({
                    "doctype": "Employee Checkin",
                    "employee": emp,
                    "time": in_time,
                    "log_type": "IN"
                }).insert(ignore_permissions=True)
            except Exception as e:
                frappe.msgprint(f"⚠️ Error parsing clock_in for {row['name']}: {e}")

        # Clock Out
        if pd.notna(row["clock_out"]) and str(row["clock_out"]).strip() != "":
            try:
                # time_part = pd.to_datetime(str(row["clock_out"])).time()
                out_time = pd.to_datetime(f"{date_part} {row['clock_out']}")
                # full_datetime = pd.to_datetime(f"{date_part} {time_part}")
                frappe.get_doc({
                    "doctype": "Employee Checkin",
                    "employee": emp,
                    "time": out_time,
                    "log_type": "OUT"
                }).insert(ignore_permissions=True)
            except Exception as e:
                frappe.msgprint(f"⚠️ Error parsing clock_out for {row['name']}: {e}")
        
        if in_time or out_time:
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
                frappe.msgprint(f"Attendance created for {row['name']} {date_part}")
            else:
                frappe.msgprint(f"Attendance already exists for {row['name']} {date_part}")

    frappe.msgprint("✅ Attendance imported successfully!")
