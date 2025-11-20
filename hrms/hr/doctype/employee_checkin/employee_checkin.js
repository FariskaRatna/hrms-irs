// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Checkin", {
	refresh: async (frm) => {
		if (frm.doc.offshift) {
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(
				__(
					"This check-in is outside assigned shift hours and will not be considered for attendance. If a shift is assigned, adjust its time window and Fetch Shift again.",
				),
			);
		}
		if (!frm.doc.__islocal) frm.trigger("add_fetch_shift_button");

		const allow_geolocation_tracking = await frappe.db.get_single_value(
			"HR Settings",
			"allow_geolocation_tracking",
		);

		if (!allow_geolocation_tracking) {
			hide_field(["fetch_geolocation", "latitude", "longitude", "geolocation"]);
			return;
		}
	},

	onload: function(frm) {
		if (!frm.is_new()) return;

		const allowed_roles = ["Administrator", "System Manager", "HR Manager"];

		for (let role of allowed_roles) {
			if (frappe.user.has_role(role)) {
				return;
			}
		}

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Leave Application",
				filters: {
					employee: frm.doc.employee,
					leave_category: "Dinas",
					status: ["not in", ["Rejected", "Cancelled"]],
					from_date: ["<=", frappe.datetime.get_today()],
					to_date: [">=", frappe.datetime.get_today()],
				},
				limit: 1
			},
			callback: function(r) {
				if (!r.message || r.message.length === 0) {
					frappe.msgprint("You don't have active Dinas Leave for this date. You cannot create an Employee Checkin.");
					frappe.set_route("List", "Employee Checkin");
					setTimeout(() => {
						frm.refresh();
					}, 10);
				}
			}
		});
	},

	fetch_geolocation: (frm) => {
		hrms.fetch_geolocation(frm);
	},

	add_fetch_shift_button(frm) {
		if (frm.doc.attendace) return;
		frm.add_custom_button(__("Fetch Shift"), function () {
			frappe.call({
				method: "fetch_shift",
				doc: frm.doc,
				freeze: true,
				freeze_message: __("Fetching Shift"),
				callback: function () {
					if (frm.doc.shift) {
						frappe.show_alert({
							message: __("Shift has been successfully updated to {0}.", [
								frm.doc.shift,
							]),
							indicator: "green",
						});
						frm.dirty();
						frm.save();
					} else {
						frappe.show_alert({
							message: __("No valid shift found for log time"),
							indicator: "orange",
						});
					}
				},
			});
		});
	},
});


// frappe.ui.form.on("Employee Checkin", {
// 	onload: function(frm) {
// 		if (!frm.is_new()) return;

// 		frappe.call({
// 			method: "frappe.client.get_list",
// 			args: {
// 				doctype: "Leave Application",
// 				filters: {
// 					employee: frm.doc.employee,
// 					leave_category: "Dinas",
// 					status: ["not in", ["Rejected", "Cancelled"]],
// 					from_date: ["<=", frappe.datetime.get_today()],
// 					to_date: [">=", frappe.datetime.get_today()],
// 				},
// 				limit: 1
// 			},
// 			callback: function(r) {
// 				if (!r.message || r.message.length === 0) {
// 					frappe.msgprint("You don't have active Dinas Leave for this date. You cannot create an Employee Checkin.");
// 					frappe.set_route("List", "Employee Checkin");
// 					setTimeout(() => {
// 						frm.refresh();
// 					}, 10);
// 				}
// 			}
// 		});
// 	}
// });