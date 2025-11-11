frappe.listview_settings["Employee Checkin"] = {
	add_fields: ["offshift"],

	get_indicator: function (doc) {
		if (doc.offshift) {
			return [__("Off-Shift"), "yellow", "offshift,=,1"];
		}
	},

	onload: function (listview) {
		// Tombol Fetch Shifts
		listview.page.add_action_item(__("Fetch Shifts"), () => {
			const checkins = listview.get_checked_items().map((checkin) => checkin.name);
			frappe.call({
				method: "hrms.hr.doctype.employee_checkin.employee_checkin.bulk_fetch_shift",
				freeze: true,
				args: {
					checkins,
				},
			});
		});

		// Tombol Sync Unlinked Attendances
		listview.page.add_inner_button(__('Sync Unlinked Attendances'), function() {
			frappe.call({
				method: "hrms.hr.doctype.employee_checkin.employee_checkin.sync_unlinked_attendances",
				freeze: true,
				freeze_message: __("Checking and creating missing attendances..."),
				callback: function(r) {
					if (r.message) {
						frappe.msgprint(r.message);
						listview.refresh();
					}
				}
			});
		}, __("Attendance Actions"));
	},
};
