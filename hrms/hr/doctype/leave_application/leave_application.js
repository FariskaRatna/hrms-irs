// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Leave Application", {
	setup: function (frm) {
		frm.set_query("leave_approver", function () {
			return {
				query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					doctype: frm.doc.doctype,
				},
			};
		});
		frm.set_query("employee", erpnext.queries.employee);
		frm._last_project_for_code = null
	},

	onload: function (frm) {
		frm._last_project_for_code = frm.doc.project || null;
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];

		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today());
		}
		if (frm.doc.docstatus == 0) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_mandatory_approval",
				args: {
					doctype: frm.doc.doctype,
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						frm.toggle_reqd("leave_approver", true);
					}
				},
			});
		}

		frm.trigger("attachment_filename");
	},

	validate: function (frm) {
		if (frm.doc.from_date === frm.doc.to_date && cint(frm.doc.half_day)) {
			frm.doc.half_day_date = frm.doc.from_date;
		} else if (frm.doc.half_day === 0) {
			frm.doc.half_day_date = "";
		}
		frm.toggle_reqd("half_day_date", cint(frm.doc.half_day));
	},

	make_dashboard: function (frm) {
		let leave_details;
		let lwps;

		if (frm.doc.employee) {
			frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
				async: false,
				args: {
					employee: frm.doc.employee,
					date: frm.doc.from_date || frm.doc.posting_date,
				},
				callback: function (r) {
					if (!r.exc && r.message["leave_allocation"]) {
						leave_details = r.message["leave_allocation"];
					}
					lwps = r.message["lwps"];
				},
			});

			$("div").remove(".form-dashboard-section.custom");

			frm.dashboard.add_section(
				frappe.render_template("leave_application_dashboard", {
					data: leave_details,
				}),
				__("Allocated Leaves"),
			);
			frm.dashboard.show();

			let allowed_leave_types = Object.keys(leave_details);
			// lwps should be allowed for selection as they don't have any allocation
			allowed_leave_types = allowed_leave_types.concat(lwps);

			frm.set_query("leave_type", function () {
				return {
					filters: [["leave_type_name", "in", allowed_leave_types]],
				};
			});
		}
	},

	refresh: function (frm) {
		// frm.page.wrapper.find(".comment-box").css({"display": "none"});
		frm.trigger("load_project_codes");
		
		hrms.leave_utils.add_view_ledger_button(frm);
		if (frm.is_new()) {
			frm.trigger("calculate_total_days");
		}

		frm.set_intro("");
		if (frm.doc.__islocal && !in_list(frappe.user_roles, "Employee")) {
			frm.set_intro(__("Fill the form and save it"));
		} else if (
			frm.perm[0] &&
			frm.perm[0].submit &&
			!frm.is_dirty() &&
			!frm.is_new() &&
			!frappe.model.has_workflow(frm.doctype) &&
			frm.doc.docstatus === 0
		) {
			frm.set_intro(__("Submit this Leave Application to confirm."));
		}

		frm.trigger("set_employee");
		if (frm.doc.docstatus === 0) {
			frm.trigger("make_dashboard");
		}
		frm.trigger("set_form_buttons");
		
		if (!frm.is_new() && frm.doc.docstatus === 0 && frm.perm[0].submit ==  1) {
			frm.page.set_primary_action(__("Submit"), function () {
				frappe.confirm(
					__("Permanently submit Leave Application for {0}?", [frm.doc.employee_name || frm.doc.employee]),
					function () {
						frappe.call({
							method: "frappe.client.submit",
							args: {
								doc: frm.doc
							},
							callback: function (r) {
								if (!r.exc) {
									frappe.show_alert({ message: __("Leave Application submitted"), indicator: "green" });
									frm.reload_doc();
								}
							}
						});
					},
					function () {
						frappe.show_alert({ message: __("Submission cancelled"), indicator: "red" });
					}
				);
			});
		}

		setTimeout(function() {
		    let save_button = frm.page.wrapper.find('.primary-action');
		    if (save_button.length > 0) {
		        save_button.hide();
		        
		        let custom_button_div = $('<div>')
		            .css({
		                'text-align': 'right',
		                'margin-top': '20px',
		                'position': 'relative',
		                'bottom': '10px',
		                'width': '100%'
		            })
		            .appendTo(frm.$wrapper.find('.form-layout'));
		            
		        save_button.appendTo(custom_button_div);
		        
		        save_button.show();
		    }
		}, 50)

		frm.set_query("project_code", () => {
			return {
				filters: {
					project: frm.doc.project
				}
			}
		});

		frm.trigger("attachment_filename");
		// frm.trigger("sync_photo_preview");
		setTimeout(() => {
            frm.trigger("attachment_filename");
        }, 100);
        
        setTimeout(() => {
            frm.trigger("attachment_filename");
        }, 300);

	},

	project(frm) {
		frm.set_value("project_code", "");
		frm.trigger("load_project_codes");
	},

	load_project_codes(frm) {
		if (!frm.doc.project) {
		frm.set_df_property("project_code", "options", []);
		frm.refresh_field("project_code");
		return;
		}

		const existing = frm.doc.project_code;

		frappe.call({
		method: "hrms.api.project_codes.get_project_codes",
		args: { project: frm.doc.project },
		callback: (r) => {
			const codes = r.message || [];

			frm.set_df_property("project_code", "options", codes.join("\n"));
			frm.refresh_field("project_code");

			// Re-apply nilai tersimpan jika masih valid
			if (existing && codes.includes(existing)) {
			frm.set_value("project_code", existing);
			}
		}
		});
	},

	sync_photo_preview: function (frm) {
		const url = frm.doc.doctor_note;
		const w = frm.fields_dict.photo_preview?.$wrapper;
		if (!w) return;

		if (!url) { 
			w.html("");
			return;
		}

		w.html(`
		<div style="margin-top:10px">
			<img src="${encodeURI(url)}"
				style="max-width:240px; max-height:240px; width:auto; height:auto;
						object-fit:contain; border-radius:10px; border:1px solid #ddd;" />
		</div>
		`);
	},

	after_save(frm) {
		frm.trigger("attachment_filename");
	},

	doctor_note(frm) {
		frm.trigger("attachment_filename");
		// frm.trigger("sync_photo_preview");
	},

	// attachment_filename: function (frm) {
	// 	const url = frm.doc.doctor_note;
	// 	const field = frm.fields_dict.doctor_note;
	// 	if (!field) return;

	// 	const $attach = $(field.$wrapper).find("a.attached-file-link");
	// 	if (!url || $attach.lenth) return;

	// 	const filename = url.split("/").pop();
	// 	$attach.text(filename);
	// 	$attach.attr("title", filename);
	// },

	attachment_filename: function(frm) {
		const url = frm.doc.doctor_note;
		const field = frm.fields_dict.doctor_note;
		if (!field) return;

		if (frm._photo_render_interval) {
			clearInterval(frm._photo_render_interval);
		}

		const forceRender = () => {
			const $wrapper = $(field.$wrapper);
			const $controlValue = $wrapper.find('.control-value');

			if (!$controlValue.length) return;

			if (url) {
				const filename = url.split("/").pop();

				$wrapper.find('a').each(function() {
					const $link = $(this);
					const text = $link.text().trim();

					if (text.includes('/') || text.includes('private') || text.includes('files')) {
						$link.text(filename);
						$link.attr('title', filename);
					}
				});
			}

			$controlValue.empty();

			if (!url) {
				if (frm.doc.docstatus !== 1) {
                    $controlValue.html(`
                        <div class="control-input" style="display: block;">
                            <div class="file-upload-area padding"></div>
                        </div>
                    `);
                    field.df.options = field.df.options || {};
                    field.refresh();
                }
                return;
			}

			const filename = url.split("/").pop();
            
            let html = '';
            
            if (frm.doc.docstatus !== 1) {
                html += `
                    <div class="attached-file" style="margin-bottom: 8px;">
                        <div class="ellipsis">
                            <i class="fa fa-paperclip"></i>
                            <a href="${url}" target="_blank" class="attached-file-link">${filename}</a>
                        </div>
                        <div class="btn-group pull-right">
                            <a class="btn btn-xs btn-default remove-attach-btn" data-file-url="${url}">
                                <i class="fa fa-times"></i>
                            </a>
                        </div>
                    </div>
                    <div class="clearfix"></div>
                    <div class="control-input" style="display: block;">
                        <div class="file-upload-area padding" style="margin-top: 10px;"></div>
                    </div>
                `;
            } else {
                html += `
                    <div class="attached-file">
                        <div class="ellipsis">
                            <i class="fa fa-paperclip"></i>
                            <a href="${url}" target="_blank" class="attached-file-link">${filename}</a>
                        </div>
                    </div>
                `;
            }

			$controlValue.html(html);

			$controlValue.find('.remove-attach-btn').on('click', function(e) {
				e.preventDefault();
				frm.set_value('doctor_note', '');
			});

			if (frm.doc.docstatus !== 1) {
                const $uploadArea = $controlValue.find('.file-upload-area');
                if ($uploadArea.length) {
                    field.setup_attach();
                }
            }
		};

		frm._photo_render_interval = setInterval(forceRender, 200);
        
        setTimeout(forceRender, 0);
        setTimeout(forceRender, 100);
        setTimeout(forceRender, 300);
	},

	async set_employee(frm) {
		if (frm.doc.employee) return;

		const employee = await hrms.get_current_employee(frm);
		if (employee) {
			frm.set_value("employee", employee);
		}
	},

	employee: function (frm) {
		frm.trigger("make_dashboard");
		frm.trigger("get_leave_balance");
		frm.trigger("set_leave_approver");

		if (!frm.doc.employee) return;

		frappe.db.get_value("Employee", frm.doc.employee, ["hrd_user"])
			.then(r => {
				frm.set_value("hrd_user", r.message.hrd_user);
			});
	},

	leave_approver: function (frm) {
		if (frm.doc.leave_approver) {
			frappe.db.get_value(
				"User",
				frm.doc.leave_approver,
				"full_name"
			).then(r => {
				if (r && r.message && r.message.full_name) {
					frm.set_value("leave_approver_name", r.message.full_name);
				}
			})
		}
	},

	leave_type: function (frm) {
		frm.trigger("get_leave_balance");
	},

	half_day: function (frm) {
		if (frm.doc.half_day) {
			if (frm.doc.from_date == frm.doc.to_date) {
				frm.set_value("half_day_date", frm.doc.from_date);
			} else {
				frm.trigger("half_day_datepicker");
			}
		} else {
			frm.set_value("half_day_date", "");
		}
		frm.trigger("calculate_total_days");
	},

	from_date: function (frm) {
		frm.events.validate_from_to_date(frm, "from_date");
		frm.trigger("make_dashboard");
		frm.trigger("half_day_datepicker");
		frm.trigger("calculate_total_days");
	},

	to_date: function (frm) {
		frm.events.validate_from_to_date(frm, "to_date");
		frm.trigger("make_dashboard");
		frm.trigger("half_day_datepicker");
		frm.trigger("calculate_total_days");
	},

	half_day_date(frm) {
		frm.trigger("calculate_total_days");
	},

	validate_from_to_date: function (frm, updated_field) {
		if (!frm.doc.from_date || !frm.doc.to_date) return;

		const from_date = Date.parse(frm.doc.from_date);
		const to_date = Date.parse(frm.doc.to_date);

		if (to_date < from_date) {
			const other_field = updated_field === "from_date" ? "to_date" : "from_date";

			frm.set_value(other_field, frm.doc[updated_field]);
			frappe.show_alert({
				message: __("Changing '{0}' to {1}.", [
					__(frm.fields_dict[other_field].df.label),
					frappe.datetime.str_to_user(frm.doc[updated_field]),
				]),
				indicator: "blue",
			});
		}
	},

	half_day_datepicker: function (frm) {
		frm.set_value("half_day_date", "");
		if (!(frm.doc.half_day && frm.doc.from_date && frm.doc.to_date)) return;

		const half_day_datepicker = frm.fields_dict.half_day_date.datepicker;
		half_day_datepicker.update({
			minDate: frappe.datetime.str_to_obj(frm.doc.from_date),
			maxDate: frappe.datetime.str_to_obj(frm.doc.to_date),
		});
	},

	get_leave_balance: function (frm) {
		if (
			frm.doc.docstatus === 0 &&
			frm.doc.employee &&
			frm.doc.leave_type &&
			frm.doc.from_date &&
			frm.doc.to_date
		) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on",
				args: {
					employee: frm.doc.employee,
					date: frm.doc.from_date,
					to_date: frm.doc.to_date,
					leave_type: frm.doc.leave_type,
					consider_all_leaves_in_the_allocation_period: 1,
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						frm.set_value("leave_balance", r.message);
					} else {
						frm.set_value("leave_balance", "0");
					}
				},
			});
		}
	},

	calculate_total_days: function (frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.employee && frm.doc.leave_type) {
			// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_number_of_leave_days",
				args: {
					employee: frm.doc.employee,
					leave_type: frm.doc.leave_type,
					from_date: frm.doc.from_date,
					to_date: frm.doc.to_date,
					half_day: frm.doc.half_day,
					half_day_date: frm.doc.half_day_date,
				},
				callback: function (r) {
					if (r && r.message) {
						frm.set_value("total_leave_days", r.message);
						frm.trigger("get_leave_balance");
					}
				},
			});
		}
	},

	set_leave_approver: function (frm) {
		if (frm.doc.employee) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_leave_approver",
				args: {
					employee: frm.doc.employee,
				},
				callback: function (r) {
					if (r && r.message) {
						frm.set_value("leave_approver", r.message);
					}
				},
			});
		}
	},

	set_form_buttons: async function (frm) {
		let self_approval_not_allowed = frm.doc.__onload
			? frm.doc.__onload.self_leave_approval_not_allowed
			: 0;
		let current_employee = await hrms.get_current_employee();
		if (
			frm.doc.docstatus === 0 &&
			!frm.is_dirty() &&
			!frappe.model.has_workflow(frm.doctype)
		) {
			if (self_approval_not_allowed && current_employee == frm.doc.employee) {
				frm.set_df_property("status", "read_only", 1);
				frm.trigger("show_save_button");
			}
		}
	},
	show_save_button: function (frm) {
		frm.page.set_primary_action("Save", () => {
			frm.save();
		});
		$(".form-message").prop("hidden", true);
	},
});

frappe.ui.form.on("Leave Application", {
	refresh(frm) {
		frm.trigger("load_project_codes");

		if (frm.doc.approval_status === "Approved") {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Employee",
					filters: { name: frm.doc.employee },
					fieldname: "user_id",
				},
				callback(r) {
					if (!r.message) return;

					const employee_user = r.message.user_id;
					const current_user = frappe.session.user;

					if (employee_user === current_user) {
						frm.set_read_only();
						frm.disable_save();
						frm.refresh_fields();
					}
				}
			});
		}
	}
});

frappe.tour["Leave Application"] = [
	{
		fieldname: "employee",
		title: "Employee",
		description: __("Select the Employee."),
	},
	{
		fieldname: "leave_type",
		title: "Leave Type",
		description: __(
			"Select type of leave the employee wants to apply for, like Sick Leave, Privilege Leave, Casual Leave, etc.",
		),
	},
	{
		fieldname: "from_date",
		title: "From Date",
		description: __("Select the start date for your Leave Application."),
	},
	{
		fieldname: "to_date",
		title: "To Date",
		description: __("Select the end date for your Leave Application."),
	},
	{
		fieldname: "half_day",
		title: "Half Day",
		description: __("To apply for a Half Day check 'Half Day' and select the Half Day Date"),
	},
	{
		fieldname: "leave_approver",
		title: "Leave Approver",
		description: __(
			"Select your Leave Approver i.e. the person who approves or rejects your leaves.",
		),
	},
];
