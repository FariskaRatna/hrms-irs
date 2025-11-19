frappe.ui.form.on("*", {
    refresh(frm) {

        // Cegah error di child table dan dokumen baru
        if (!frm.doc || frm.is_new()) return;

        // --- 1. Lock dokumen jika status Approved ---
        if (frm.doc.status === "Approved") {
            frm.set_read_only();
            frm.disable_save();

            // Lock semua field
            Object.keys(frm.fields_dict).forEach((f) => {
                frm.set_df_property(f, "read_only", 1);
            });

            console.log("[Global Lock] →", frm.doctype, frm.doc.name);
        }

        // --- 2. Lock field ID buatan kamu (jika ada) ---
        // contoh kalau kamu punya field custom bernama "document_id"
        if (frm.fields_dict["naming_series"]) {
            frm.set_df_property("naming_series", "read_only", 1);
        }
    },
});
