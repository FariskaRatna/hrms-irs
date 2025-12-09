frappe.listview_settings["Overtime"] = {
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
        })
    }
}