import frappe
from frappe.model.document import Document
from frappe.utils import add_months, getdate
from frappe import _


class OvertimeSlip(Document):
	MAX_MONTHLY_OVERTIME = 72

	def before_save(self):
		if getattr(self.flags, "skip_split_overtime", False):
			return
		
		self.create_overtime_record()
		# self.sort_overtime_desc()
		self.split_overtime()

	def before_insert(self):
		# self.apply_previous_overtime()
		pass

	def create_overtime_record(self):
		calculations = frappe.get_all(
			"Overtime Calculation",
			filters={
				"employee": self.employee,
				"date": ["between", [self.from_date, self.to_date]],
				"approval_status": "Approved",
			},
			fields=["name", "date", "day_type", "total_hours", "total_amount"]
		)

		existing = {d.overtime_calculation for d in self.overtime_summary}

		for c in calculations:
			if c.name not in existing:
				row = self.append("overtime_summary", {})
				row.overtime_calculation = c.name
				row.date = c.date
				row.day_type = c.day_type
				row.total_hours = c.total_hours
				row.amount = c.total_amount

	def sort_overtime_desc(self):
		rows = list(self.overtime_summary)

		rows.sort(key=lambda x: x.date, reverse=True)

		self.set("overtime_summary", [])

		for r in rows:
			row = self.append("overtime_summary", {})
			row.overtime_calculation = r.overtime_calculation
			row.date = r.date
			row.day_type = r.day_type
			row.total_hours = r.total_hours
			row.amount = r.amount


	# def split_overtime(self):
	# 	sorted_items = sorted(list(self.overtime_summary), key=lambda x: x.date)

	# 	# Reset perhitungan
	# 	self.total_hours = 0
	# 	self.total_amount = 0

	# 	total_used = 0
	# 	last_item = sorted_items[-1]  

	# 	total_hours_sum = sum(item.total_hours or 0 for item in sorted_items)

	# 	if total_hours_sum > self.MAX_MONTHLY_OVERTIME:
	# 		excess = total_hours_sum - self.MAX_MONTHLY_OVERTIME

	# 		used_last = max((last_item.total_hours or 0) - excess, 0)
	# 		carry = (last_item.total_hours or 0) - used_last
	# 	else:
	# 		used_last = last_item.total_hours or 0
	# 		carry = 0

	# 	for item in sorted_items:
	# 		if item == last_item:
	# 			item.total_hours = used_last
	# 		amount = self.calculate_amount(item.total_hours, item.day_type)
	# 		item.amount = amount
	# 		self.total_hours += item.total_hours
	# 		self.total_amount += item.amount

	# 	self.set("overtime_summary", [])
	# 	for item in sorted_items:
	# 		row = self.append("overtime_summary", {})
	# 		row.overtime_calculation = item.overtime_calculation
	# 		row.date = item.date
	# 		row.day_type = item.day_type
	# 		row.total_hours = item.total_hours
	# 		row.amount = item.amount

	# 	if carry > 0:
	# 		self.create_next_month_slip([self._carry_data(last_item, carry)])

	def split_overtime(self):
		items = sorted(list(self.overtime_summary), key=lambda x: x.date)

		# Reset dulu
		self.total_hours = 0
		self.total_amount = 0

		used_rows = []
		carry_rows = []

		used_total = 0.0
		max_h = float(self.MAX_MONTHLY_OVERTIME)

		for it in items:
			hours = float(it.total_hours or 0)
			if hours <= 0:
				continue

			remaining = max_h - used_total

			# Jika quota slip ini sudah habis, semua masuk carry
			if remaining <= 0:
				carry_rows.append(self._carry_data(it, hours))
				continue

			if hours <= remaining:
				# masuk semua ke slip ini
				used_rows.append({
					"overtime_calculation": it.overtime_calculation,
					"date": it.date,
					"day_type": it.day_type,
					"hours": hours,
				})
				used_total += hours
			else:
				# split: sebagian masuk slip ini, sisanya carry
				used_part = remaining
				carry_part = hours - remaining

				if used_part > 0:
					used_rows.append({
						"overtime_calculation": it.overtime_calculation,
						"date": it.date,
						"day_type": it.day_type,
						"hours": used_part,
					})
					used_total += used_part

				if carry_part > 0:
					carry_rows.append(self._carry_data(it, carry_part))

		# Rebuild child table untuk slip saat ini
		self.set("overtime_summary", [])

		total_hours = 0.0
		total_amount = 0.0

		for r in used_rows:
			amount = self.calculate_amount(r["hours"], r["day_type"])

			row = self.append("overtime_summary", {})
			row.overtime_calculation = r["overtime_calculation"]
			row.date = r["date"]
			row.day_type = r["day_type"]
			row.total_hours = r["hours"]
			row.amount = amount

			total_hours += r["hours"]
			total_amount += amount

		self.total_hours = total_hours
		self.total_amount = total_amount

		# Jika ada carry, buat / update slip periode berikutnya
		if carry_rows:
			self.create_next_month_slip(carry_rows)


	# def _carry_data(self, item, carry_hours):
	# 	return {
	# 		"hours": carry_hours,
	# 		"day_type": item.day_type,
	# 		"date": item.date,
	# 		"original_calculation": item.overtime_calculation,
	# 	}

	def _carry_data(self, item, carry_hours):
		return {
			"hours": float(carry_hours),
			"day_type": item.day_type,
			"date": item.date,
			"original_calculation": item.overtime_calculation,
		}



	def calculate_amount(self, hours, day_type):
		calc = frappe.new_doc("Overtime Calculation")
		calc.employee = self.employee
		calc.total_hours = hours
		calc.day_type = day_type
		calc.calculate_overtime_pay()
		return calc.total_amount

	# def create_next_month_slip(self, carries):
	# 	next_slip = frappe.new_doc("Overtime Slip")
	# 	next_slip.employee = self.employee
	# 	next_slip.from_date = add_months(getdate(self.from_date), 1).replace(day=21)
	# 	next_slip.to_date = add_months(getdate(self.to_date), 1).replace(day=20)
	# 	next_slip.excess_from_reference = self.name

	# 	total_hours = 0
	# 	total_amount = 0

	# 	for c in carries:
	# 		hours = c["hours"]
	# 		day_type = c["day_type"]
	# 		amount = self.calculate_amount(hours, day_type)

	# 		row = next_slip.append("overtime_summary", {})
	# 		row.overtime_calculation = c["original_calculation"]
	# 		row.date = c["date"]
	# 		row.day_type = day_type
	# 		row.total_hours = hours
	# 		row.amount = amount

	# 		total_hours += hours
	# 		total_amount += amount

	# 	next_slip.total_hours = total_hours
	# 	next_slip.total_amount = total_amount

	# 	next_slip.insert(ignore_permissions=True)
	# 	frappe.msgprint(_("{0} excess hours moved to next month.").format(total_hours))

	def create_next_month_slip(self, carries):
		next_from = add_months(getdate(self.from_date), 1).replace(day=21)
		next_to = add_months(getdate(self.to_date), 1).replace(day=20)

		# Cari slip bulan depan yang sudah ada (Draft) untuk employee & periode ini
		existing_name = frappe.db.get_value(
			"Overtime Slip",
			{
				"employee": self.employee,
				"from_date": next_from,
				"to_date": next_to,
				"docstatus": 0,
			},
			"name",
		)

		if existing_name:
			next_slip = frappe.get_doc("Overtime Slip", existing_name)
			# penting: jangan jalankan split_overtime lagi saat save/insert
			next_slip.flags.skip_split_overtime = True
			next_slip.excess_from_reference = self.name
			next_slip.set("overtime_summary", [])
		else:
			next_slip = frappe.new_doc("Overtime Slip")
			next_slip.flags.skip_split_overtime = True
			next_slip.employee = self.employee
			next_slip.from_date = next_from
			next_slip.to_date = next_to
			next_slip.excess_from_reference = self.name

		total_hours = 0.0
		total_amount = 0.0

		for c in carries:
			hours = float(c["hours"] or 0)
			if hours <= 0:
				continue

			day_type = c["day_type"]
			amount = self.calculate_amount(hours, day_type)

			row = next_slip.append("overtime_summary", {})
			row.overtime_calculation = c["original_calculation"]
			row.date = c["date"]
			row.day_type = day_type
			row.total_hours = hours
			row.amount = amount

			total_hours += hours
			total_amount += amount

		next_slip.total_hours = total_hours
		next_slip.total_amount = total_amount

		if existing_name:
			next_slip.save(ignore_permissions=True)
		else:
			next_slip.insert(ignore_permissions=True)

		frappe.msgprint(_("{0} excess hours moved to next month.").format(total_hours))


	def apply_previous_overtime(self):
		previous = frappe.db.sql("""
			SELECT name, total_hours, total_amount
			FROM `tabOvertime Slip`
			WHERE employee = %s AND docstatus = 1
			ORDER BY to_date DESC LIMIT 1
		""", (self.employee,), as_dict=True)

		if previous:
			self.total_hours = (self.total_hours or 0) + previous[0].total_hours
			self.total_amount = (self.total_amount or 0) + previous[0].total_amount
