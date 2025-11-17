frappe.ui.form.on("*", {
    refresh(frm) {
        // Cegah infinite loop di child table
        if (!frm.doc || frm.is_new()) return;

        if (frm.doc.status === "Approved") {
            frm.set_read_only();
            frm.disable_save();

            // force re-render fields menjadi grey
            for (let field in frm.fields_dict) {
                frm.fields_dict[field].df.read_only = 1;
                frm.fields_dict[field].refresh();
            }

            console.log("Global Lock →", frm.doctype, frm.doc.name);
        }
    },
});
