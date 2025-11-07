frappe.after_ajax(() => {
    // interval untuk nunggu workspace HR siap
    const interval = setInterval(() => {
        const route = frappe.get_route();
        const body = document.querySelector(".workspace-body");

        if (route[0] === "workspace" && route[1] === "HR" && body) {
            clearInterval(interval);

            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Note",
                    filters: { public: 1 },
                    fields: ["name", "title", "content", "modified"],
                    order_by: "modified desc",
                    limit_page_length: 5
                },
                callback: function(r) {
                    if (r.message && r.message.length) {
                        let html = `
                            <div class="frappe-card" style="margin-bottom: 16px;">
                                <div class="frappe-card-head" style="font-weight: 600; font-size: 1.1rem;">
                                    📢 Pengumuman Perusahaan
                                </div>
                                <ul style="margin-top: 8px;">
                        `;
                        r.message.forEach(note => {
                            html += `
                                <li style="margin-bottom: 6px;">
                                    <a href="/app/note/${note.name}" style="font-weight: 500;">
                                        ${note.title}
                                    </a>
                                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                                        ${frappe.datetime.str_to_user(note.modified)}
                                    </div>
                                </li>
                            `;
                        });
                        html += `</ul></div>`;

                        // masukkan pengumuman ke atas workspace
                        body.insertAdjacentHTML("afterbegin", html);
                    }
                }
            });
        }
    }, 500); // cek setiap 0.5 detik
});
