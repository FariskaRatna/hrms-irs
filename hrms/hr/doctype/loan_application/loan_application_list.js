frappe.listview_settings["Loan Application"] = {
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
        }, 0)
    }
}