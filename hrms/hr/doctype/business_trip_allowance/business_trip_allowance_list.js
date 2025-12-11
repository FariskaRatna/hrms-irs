frappe.listview_settings["Business Trip Allowance"] = {
    refresh: listview => {
        $('span.level-item.list-liked-by-me.hidden-xs').remove();
        $('span.list-row-like.hidden-xs').remove();
        $('span.comment-count.d-flex.align-items-center').remove();
        $('span.mx-2').remove();

        function apply_layout() {
            $('.list-row .level-right').css({
                "flex": "0 0 70px",
                "max-width": "70px",
                "padding": "0 4px",
                "margin": "0",
                "text-align": "right",
                "white-space":"nowrap",
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

            $('.list-row-col[data-fieldname="docstatus"]').css({
                "flex": "0 0 140px",
                "max-width": "140px",
                "white-space": "nowrap"
            });

             $('.list-row-col[data-fieldname="business-trip"]').css({
                "flex": "0 0 260px",
                "max-width": "260px",
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
}