frappe.ui.form.on('Job Card', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus ==0 && frm.doc.total_completed_qty < frm.doc.for_quantity) {
            frm.add_custom_button("Transfer RM", () => {
                frm.trigger("open_rm_selection_popup");
            });
        }
    },

    open_rm_selection_popup(frm) {
        frappe.call({
            method: "opus.overrides.py.job_card.get_mtfm_items",
            args: { work_order: frm.doc.work_order },
            freeze: true,
            freeze_message: "Fetching RM from MTFM..."
        }).then(r => {
            const items = r.message;

            if (!items || items.length === 0) {
                frappe.msgprint("No Material Transfer for Manufacture found.");
                return;
            }

            // Build fields for dialog
            let fields = items.map((d, i) => ({
                fieldname: "item_" + i,
                label: `${d.item_code} (Qty: ${d.allowed_qty})`,
                fieldtype: "Float",
                default: 0,
                reqd: 0
            }));

            const d = new frappe.ui.Dialog({
                title: "Select RM to Transfer",
                fields: fields,
                primary_action_label: "Create Transfer Entry",
                primary_action(values) {
                    let selected = [];

                    items.forEach((row, i) => {
                        let entered_qty = values["item_" + i];
                        if (entered_qty && entered_qty > 0) {
                            selected.push({
                                item_code: row.item_code,
                                allowed_qty: row.allowed_qty,
                                qty: entered_qty,
                                uom: row.uom,
                                stock_uom: row.stock_uom,
                                conversion_factor: row.conversion_factor,
                                s_warehouse: row.s_warehouse,
                                t_warehouse: row.t_warehouse,
                                serial_and_batch_bundle: row.serial_and_batch_bundle
                            });
                        }
                    });

                    if (selected.length === 0) {
                        frappe.msgprint("No RM selected!");
                        return;
                    }

                    // Send data to backend
                    frappe.call({
                        method: "opus.overrides.py.job_card.create_material_transfer",
                        args: {
                            work_order: frm.doc.work_order,
                            items: selected,
                            job_card: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: "Creating Material Transfer..."
                    }).then(res => {
                        d.hide();
                        
                    });
                }
            });

            d.show();
        });
    }
});
