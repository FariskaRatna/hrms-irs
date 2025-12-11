frappe.listview_settings["Overtime Slip"] = {
    add_fields: [
        "from_date",
        "to_date",
        "total_hours",
    ],
    has_indicator_for_draft: 1,
    get_indicator: function (doc) {
        const color_status = {
            "Approved": "green",
            "Rejected": "red",
            "Draft": "yellow",
            "Cancelled": "orange",
            "Submitted": "blue"
        };
        const status =
            !doc.docstatus && ["Approved", "Rejected"].includes(doc.status) ? "Draft" : doc.status;
        return [__(status), status_color[status], "status,=," + doc.status];
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
            setTimeout(apply_layout, 50)
        }

    }
}