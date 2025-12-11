frappe.listview_settings["Reimbursement"] = {
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
            if (value === "Pending") {
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
}