frappe.listview_settings["Business Trip"] = {
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

    refresh: listview => {
        $('span.level-item.list-liked-by-me.hidden-xs').remove();
        $('span.list-row-like.hidden-xs').remove();
        $('span.comment-count.d-flex.align-items-center').remove();
        $('span.mx-2').remove();

        setTimeout(() => {
            $('.list-row .level-right').css({
                "flex": "0 0 80px",
                "max-width": "80px",
                "padding": "0 4px",
                "margin": "0",
                "text-align": "right",
                "white-space":"nowrap",
                "overflow": "hidden"
            })

            $('.list-row-head .level-right').css({
                "flex": "0 0 80px",
                "max-width": "80px",
                "padding": "0 4px",
                "margin": "0",
                "text-align": "right",
                "white-space": "nowrap",
                "overflow": "hidden"
            });

            $('.list-row-head .list-row-col').eq(2).css({
                "flex": "0 0 120px",
                "max-width": "140px",
                "white-space": "nowrap",
            });

            $('.list-row-container .list-row').each(function () {
                $(this).find('.list-row-col').eq(2).css({
                    "flex": "0 0 120px",
                    "max-width": "140px",
                    "white-space": "nowrap",
                });
            });


            $('.list-row-head .list-row-col').eq(4).css({
                "flex": "0 0 80px",
                "max-width": "100px",
                "white-space": "nowrap",
            });

            $('.list-row-container .list-row').each(function () {
                $(this).find('.list-row-col').eq(4).css({
                    "flex": "0 0 80px",
                    "max-width": "100px",
                    "white-space": "nowrap",
                });
            });

            $('.list-row-head .list-row-col').eq(6).css({
                "flex": "0 0 160px",
                "max-width": "180px",
                "white-space": "nowrap",
            });

            $('.list-row-container .list-row').each(function () {
                $(this).find('.list-row-col').eq(6).css({
                    "flex": "0 0 160px",
                    "max-width": "180px",
                    "white-space": "nowrap",
                });
            });
        })
    }
}