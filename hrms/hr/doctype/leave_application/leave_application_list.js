// Untuk tampilan status pada leave application, tidak digunakan karena yang digunakan yang approval status

// frappe.listview_settings["Leave Application"] = {
// 	add_fields: [
// 		"leave_type",
// 		"employee",
// 		"employee_name",
// 		"total_leave_days",
// 		"from_date",
// 		"to_date",
// 	],
// 	has_indicator_for_draft: 1,
// 	get_indicator: function (doc) {
// 		const status_color = {
// 			// Approved: "green",
// 			// Rejected: "red",
// 			// Open: "orange",
// 			Draft: "red",
// 			Cancelled: "red",
// 			Submitted: "blue",
// 		};
// 		const status =
// 			!doc.docstatus && ["Approved", "Rejected"].includes(doc.approval_status) ? "Draft" : doc.approval_status;
// 		return [__(status), status_color[status], "status,=," + doc.approval_status];
// 	},
// };

// frappe.listview_settings["Leave Application"] = {
//     refresh: litview => {
//         $('span.level-item.list-liked-by-me.hidden-xs').remove();
//         $('span.list-row-like.hidden-xs').remove();
//         $('span.comment-count.d-flex.align-items-center').remove();
//         $('span.mx-2').remove();

//         // $('div.list-row-container .list-row-col:last-child').css("flex", " 0 0 180px");
//     }
// };


frappe.listview_settings["Leave Application"] = {
    refresh: listview => {

        $('span.level-item.list-liked-by-me.hidden-xs').remove();
        $('span.list-row-like.hidden-xs').remove();
        $('span.comment-count.d-flex.align-items-center').remove();
        $('span.mx-2').remove();

        setTimeout(() => {
            $('.list-row .level-right').css({
                "flex": "0 0 70px",
                "max-width": "70px",
                "padding": "0 4px",
                "margin": "0",
                "text-align": "right",
                "white-space": "nowrap",
                "overflow": "hidden"
            });

            $('.list-row-head .level-right').css({
                "flex": "0 0 70px",
                "max-width": "70px",
                "padding": "0 4px",
                "margin": "0",
                "text-align": "right",
                "white-space": "nowrap",
                "overflow": "hidden"
            });

            $('.list-row-head .list-row-col').eq(5).css({
                "flex": "0 0 160px",
                "max-width": "200px",
                "white-space": "nowrap",
            });

            $('.list-row-container .list-row').each(function () {
                $(this).find('.list-row-col').eq(5).css({
                    "flex": "0 0 160px",
                    "max-width": "200px",
                    "white-space": "nowrap",
                });
            });

            $('.list-row-head .list-row-col').eq(6).css({
                "flex": "0 0 180px",
                "max-width": "200px",
                "white-space": "nowrap",
            });

            $('.list-row-container .list-row').each(function () {
                $(this).find('.list-row-col').eq(6).css({
                    "flex": "0 0 180px",
                    "max-width": "200px",
                    "white-space": "nowrap",
                });
            });

        }, 0);
    }
};



