frappe.ui.form.on('Job Card', {
    refresh(frm) {
        // Transfer RM button (existing)
        if (!frm.is_new() && frm.doc.docstatus == 0 && frm.doc.total_completed_qty < frm.doc.for_quantity) {
            frm.add_custom_button("Transfer RM", () => {
                frm.trigger("open_rm_selection_popup");
            });

            if (frm.doc.total_completed_qty > 0) {
                frm.add_custom_button(__("Force Submit"), () => {
                    const d = new frappe.ui.Dialog({
                        title: __('Force Submit Job Card'),
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'message',
                                options: `<div style="margin-bottom: 10px;">${__("You are about to submit this Job Card with a partial completed quantity.")}</div>
                                          <div><b>${__("Planned Qty:")}</b> ${frm.doc.for_quantity}</div>
                                          <div><b>${__("Completed Qty:")}</b> ${frm.doc.total_completed_qty}</div>
                                          <br>
                                          <div>${__("Are you sure you want to force submit?")}</div>`
                            }
                        ],
                        primary_action_label: __('Submit'),
                        primary_action_classes: 'btn-danger',
                        primary_action(values) {
                            d.hide();
                            frappe.dom.freeze(__('Submitting...'));
                            frappe.call({
                                method: 'opus.overrides.py.job_card.force_submit_job_card',
                                args: {
                                    job_card: frm.doc.name
                                },
                                callback: function(r) {
                                    frappe.dom.unfreeze();
                                    if(!r.exc) {
                                        frm.reload_doc();
                                        frappe.show_alert({message: __('Job Card Successfully Completed'), indicator: 'green'});
                                    }
                                },
                                error: function(r) {
                                    frappe.dom.unfreeze();
                                }
                            });
                        }
                    });
                    d.show();
                }).removeClass('btn-default').addClass('btn-danger');
            }
        }

        // Remove standard buttons to prevent duplicates and glitches
        frm.remove_custom_button(__("Start Job"));
        frm.remove_custom_button(__("Complete Job"));

        // Logic to show "Start Job" or "Complete Job"
        let last_log = frm.doc.time_logs && frm.doc.time_logs.length > 0 ? frm.doc.time_logs[frm.doc.time_logs.length - 1] : null;
        let is_running = last_log && !last_log.to_time;
        let remaining = flt(frm.doc.for_quantity) - flt(frm.doc.total_completed_qty);
        
        if (frm.doc.docstatus === 0 && remaining > 0) {
            if (!is_running) {
                frm.add_custom_button(__("Start Job"), () => {
                    let from_time = frappe.datetime.now_datetime();
                    if ((frm.doc.employee && !frm.doc.employee.length) || !frm.doc.employee) {
                        frappe.prompt(
                            {
                                fieldtype: "Table MultiSelect",
                                label: __("Select Employees"),
                                options: "Job Card Time Log",
                                fieldname: "employees",
                                reqd: 1,
                                filters: { status: "Active" },
                            },
                            (d) => {
                                frm.events.start_job(frm, "Work In Progress", d.employees);
                            },
                            __("Assign Job to Employee")
                        );
                    } else {
                        frm.events.start_job(frm, "Work In Progress", frm.doc.employee);
                    }
                }).removeClass('btn-default').addClass('btn-primary');
            } else {
                frm.add_custom_button(__("Complete Job"), () => {
                    frm.events.complete_job_card(frm);
                }).removeClass('btn-default').addClass('btn-primary');
            }
        }
    },

    complete_job_card(frm) {
		let fields = [
			{
				fieldtype: "Float",
				label: __("Qty to Manufacture"),
				fieldname: "for_quantity",
				reqd: 1,
				default: frm.doc.for_quantity,
				change() {
					let doc = frm.job_completion_dialog;

					doc.set_value("completed_qty", doc.get_value("for_quantity"));
					doc.set_value("process_loss_qty", 0);
				},
			},
			{
				fieldtype: "Float",
				label: __("Completed Quantity"),
				fieldname: "completed_qty",
				reqd: 1,
				default: frm.doc.for_quantity - frm.doc.total_completed_qty,
				change() {
					let doc = frm.job_completion_dialog;

					let process_loss_qty = doc.get_value("for_quantity") - doc.get_value("completed_qty");
					if (process_loss_qty > 0 && process_loss_qty != doc.get_value("process_loss_qty")) {
						doc.set_value("process_loss_qty", process_loss_qty);
					}
				},
			},
			{
				fieldtype: "Float",
				label: __("Process Loss Quantity"),
				fieldname: "process_loss_qty",
				onchange() {
					let doc = frm.job_completion_dialog;

					let completed_qty = doc.get_value("for_quantity") - doc.get_value("process_loss_qty");
					doc.set_value("completed_qty", completed_qty);
				},
			},
			{
				fieldtype: "Section Break",
			},
		];

		if (frm.doc.sub_operations && frm.doc.sub_operations.length) {
			fields.push({
				fieldtype: "Link",
				label: __("Sub Operation"),
				fieldname: "sub_operation",
				options: "Operation",
				get_query() {
					let non_completed_operations = frm.doc.sub_operations.filter(
						(d) => d.status === "Pending"
					);
					return {
						filters: {
							name: ["in", non_completed_operations.map((d) => d.sub_operation)],
						},
					};
				},
				reqd: 1,
			});
		}

		let last_completed_row = frm.doc.time_logs ? frm.doc.time_logs.filter((d) => d.to_time).pop() : null;
		let last_row = frm.doc.time_logs && frm.doc.time_logs.length ? frm.doc.time_logs[frm.doc.time_logs.length - 1] : {};
		
		if (!last_completed_row || !last_completed_row.to_time || !last_row.to_time) {
			fields.push({
				fieldtype: "Datetime",
				label: __("End Time"),
				fieldname: "end_time",
				default: frappe.datetime.now_datetime(),
			});
		}

		frm.job_completion_dialog = frappe.prompt(
			fields,
			(data) => {
				if (data.completed_qty <= 0) {
					frappe.throw(__("Quantity should be greater than 0"));
				}

                frappe.dom.freeze(__('Saving & creating Stock Entry...'));
                frappe.call({
                    method: 'opus.overrides.py.job_card.make_time_log',
                    args: {
                        args: {
                            job_card_id:   frm.doc.name,
                            completed_qty: data.completed_qty,
                            for_quantity:  data.for_quantity,
                            process_loss_qty: data.process_loss_qty,
                            complete_time: data.end_time || frappe.datetime.now_datetime(),
                            sub_operation: data.sub_operation,
                            action:        'Complete',
                        }
                    },
                    callback(r) {
                        frappe.dom.unfreeze();
                        frm.reload_doc();
                    },
                    error() {
                        frappe.dom.unfreeze();
                        frm.reload_doc();
                    }
                });
			},
			__("Enter Value"),
			__("Update"),
			__("Set Finished Good Quantity")
		);
	}
});



// Transfer RM popup (unchanged from original)
frappe.ui.form.on('Job Card', {
    open_rm_selection_popup(frm) {
        frappe.call({
            method: 'opus.overrides.py.job_card.get_mtfm_items',
            args: { work_order: frm.doc.work_order },
            freeze: true,
            freeze_message: 'Fetching RM from MTFM...'
        }).then(r => {
            const items = r.message;

            if (!items || items.length === 0) {
                frappe.msgprint('No Material Transfer for Manufacture found.');
                return;
            }

            let fields = items.map((d, i) => ({
                fieldname: 'item_' + i,
                label: `${d.item_code} (Qty: ${d.allowed_qty})`,
                fieldtype: 'Float',
                default: 0,
                reqd: 0
            }));

            const d = new frappe.ui.Dialog({
                title: 'Select RM to Transfer',
                fields: fields,
                primary_action_label: 'Create Transfer Entry',
                primary_action(values) {
                    let selected = [];

                    items.forEach((row, i) => {
                        let entered_qty = values['item_' + i];
                        if (entered_qty && entered_qty > 0) {
                            selected.push({
                                item_code:               row.item_code,
                                allowed_qty:             row.allowed_qty,
                                qty:                     entered_qty,
                                uom:                     row.uom,
                                stock_uom:               row.stock_uom,
                                conversion_factor:       row.conversion_factor,
                                s_warehouse:             row.s_warehouse,
                                t_warehouse:             row.t_warehouse,
                                serial_and_batch_bundle: row.serial_and_batch_bundle
                            });
                        }
                    });

                    if (selected.length === 0) {
                        frappe.msgprint('No RM selected!');
                        return;
                    }

                    frappe.call({
                        method: 'opus.overrides.py.job_card.create_material_transfer',
                        args: {
                            work_order: frm.doc.work_order,
                            items:      selected,
                            job_card:   frm.doc.name
                        },
                        freeze: true,
                        freeze_message: 'Creating Material Transfer...'
                    }).then(res => {
                        d.hide();
                    });
                }
            });

            d.show();
        });
    }
});