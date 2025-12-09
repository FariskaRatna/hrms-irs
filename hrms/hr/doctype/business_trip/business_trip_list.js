frappe.listview_settings["Business Trip"] = {
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