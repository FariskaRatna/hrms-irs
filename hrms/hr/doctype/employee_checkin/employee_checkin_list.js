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

        setTimeout(() => {
            $('.list-row .level-right, .list-row-head .level-right').css({
                flex: "0 0 70px",
                "max-width": "70px",
                "padding": "0 4px",
                "margin": "0",
                "text-align": "right",
                "white-space": "nowrap",
                "overflow": "hidden"
            });

            $('.list-row-head .list-row-col').eq(2).css({
                "flex": "0 0 100px",
                "max-width": "100px",
                "white-space": "nowrap",
            });

            $('.list-row-container .list-row').each(function () {
                $(this).find('.list-row-col').eq(2).css({
                    "flex": "0 0 100px",
                    "max-width": "100px",
                    "white-space": "nowrap",
                });
            });

			$('.list-row-head .list-row-col').eq(3).css({
                "flex": "0 0 160px",
                "max-width": "160px",
                "white-space": "nowrap",
            });

            $('.list-row-container .list-row').each(function () {
                $(this).find('.list-row-col').eq(3).css({
                    "flex": "0 0 160px",
                    "max-width": "160px",
                    "white-space": "nowrap",
                });
            });

            $('.list-row-head .list-row-col').eq(5).css({
                "flex": "0 0 230px",
                "max-width": "230px",
                "white-space": "nowrap",
            });

            $('.list-row-container .list-row').each(function () {
                $(this).find('.list-row-col').eq(5).css({
                    "flex": "0 0 230px",
                    "max-width": "230px",
                    "white-space": "nowrap",
                });
            });

            // kalau kolom ID adalah list-subject, paksa juga di sini
            $('.list-row .list-row-col.list-subject').css({
                "flex": "0 0 230px",
                "max-width": "230px",
                "white-space": "nowrap"
            });
        }, 0);
	}
};
