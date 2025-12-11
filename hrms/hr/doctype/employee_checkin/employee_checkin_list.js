frappe.listview_settings["Employee Checkin"] = {
	add_fields: ["offshift"],

	get_indicator: function (doc) {
		if (doc.offshift) {
			return [__("Off-Shift"), "yellow", "offshift,=,1"];
		}
	},

	onload: function (listview) {
		listview.page_length = 100;
		$('button[data-value="20"]').removeClass("btn-info");
		$('button[data-calue="100"]').addClass("btn-info");
		listview.refresh();

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
	},

	refresh: listview => {
		$('span.level-item.list-liked-by-me.hidden-xs').remove();
        $('span.list-row-like.hidden-xs').remove();
        $('span.comment-count.d-flex.align-items-center').remove();
        $('span.mx-2').remove();

        function apply_layout() {
            $('.list-row .level-right, .list-row-head .level-right').css({
                "flex": "0 0 70px",
                "max-width": "70px",
                "padding": "0 4px",
                "margin": "0",
                "text-align": "right",
                "white-space": "nowrap",
                "overflow": "hidden"
            });

            $('.list-row-col[data-fieldname="name"]').css({
                "flex": "0 0 260px",     
                "max-width": "260px",
                "white-space": "nowrap"
            });

            $('.list-row-col.list-subject').css({
                "flex": "0 0 260px",
                "max-width": "260px",
                "white-space": "nowrap"
            });
        }

        if (listview.on_rendered) {
            listview.on_rendered = apply_layout;
        } else {
            setTimeout(apply_layout, 50);
        }
	}
};
