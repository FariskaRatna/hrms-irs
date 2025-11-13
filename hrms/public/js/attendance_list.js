frappe.listview_settings["Attendance"] = {
    onload(listview) {
        // Tunggu sampai DOM selesai, lalu hapus badge Submitted
        listview.page.wrapper.on("DOMSubtreeModified", function () {
            listview.$result.find(".list-row .indicator-pill:contains('Submitted')").remove();
        });
    },

    get_indicator: function (doc) {
        if (doc.status === "Present") {
            return [__("Present"), "green", "status,=,Present"];
        } else if (doc.status === "Absent") {
            return [__("Absent"), "red", "status,=,Absent"];
        } else if (doc.status === "On Leave") {
            return [__("On Leave"), "orange", "status,=,On Leave"];
        } else {
            return [__("Draft"), "gray", "docstatus,=,0"];
        }
    },
};
