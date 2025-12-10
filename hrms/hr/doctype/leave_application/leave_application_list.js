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
    add_fields: ["approval_status", "docstatus"],
    
    has_indicator_for_draft: 1,
    get_indicator: function (doc) {
        if (doc.docstatus === 0) {
            return [__("Draft"), "yellow", "docstatus,=,0"];
        }
        if (doc.docstatus === 1) {
            return [__("Submitted"), "blue", "docstatus,=,1"];
        }
        if (doc.docstatus === 2) {
            return [__("Cancelled"), "red", "docstatus,=,2"];
        }
    },

    formatters: {
        approval_status: function (value, df, options, doc) {
            if (!value) return "";

            var color = "gray";
            if (value === "Open") {
                color = "orange";
            } else if (value === "Approved") {
                color = "green";
            } else if (value === "Rejected") {
                color = "red";
            }
            
            return (
                '<span class="indicator-pill whitespace-nowrap ' + color + '">' +
                    '<span class="hidden-xs">' + frappe.utils.escape_html(__(value)) + "</span>" +
                "</span>"
            );
        }
    },


    // refresh: listview => {

    //     $('span.level-item.list-liked-by-me.hidden-xs').remove();
    //     $('span.list-row-like.hidden-xs').remove();
    //     $('span.comment-count.d-flex.align-items-center').remove();
    //     $('span.mx-2').remove();

    //     setTimeout(() => {
    //         $('.list-row .level-right').css({
    //             "flex": "0 0 70px",
    //             "max-width": "70px",
    //             "padding": "0 4px",
    //             "margin": "0",
    //             "text-align": "right",
    //             "white-space": "nowrap",
    //             "overflow": "hidden"
    //         });

    //         $('.list-row-head .level-right').css({
    //             "flex": "0 0 70px",
    //             "max-width": "70px",
    //             "padding": "0 4px",
    //             "margin": "0",
    //             "text-align": "right",
    //             "white-space": "nowrap",
    //             "overflow": "hidden"
    //         });

    //         $('.list-row-head .list-row-col').eq(5).css({
    //             "flex": "0 0 160px",
    //             "max-width": "200px",
    //             "white-space": "nowrap",
    //         });

    //         $('.list-row-container .list-row').each(function () {
    //             $(this).find('.list-row-col').eq(5).css({
    //                 "flex": "0 0 160px",
    //                 "max-width": "200px",
    //                 "white-space": "nowrap",
    //             });
    //         });

    //         $('.list-row-head .list-row-col').eq(6).css({
    //             "flex": "0 0 180px",
    //             "max-width": "200px",
    //             "white-space": "nowrap",
    //         });

    //         $('.list-row-container .list-row').each(function () {
    //             $(this).find('.list-row-col').eq(6).css({
    //                 "flex": "0 0 180px",
    //                 "max-width": "200px",
    //                 "white-space": "nowrap",
    //             });
    //         });

    //     }, 0);
    // }

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

            $('.list-row-col[data-fieldname="leave_category"]').css({
                "flex": "0 0 180px",
                "max-width": "200px",
                "white-space": "nowrap"
            });

            $('.list-row-col[data-fieldname="name"]').css({
                "flex": "0 0 280px",     
                "max-width": "280px",
                "white-space": "nowrap"
            });

            $('.list-row-col.list-subject').css({
                "flex": "0 0 280px",
                "max-width": "280px",
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



