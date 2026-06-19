from erpnext.manufacturing.doctype.job_card.job_card import JobCard
import frappe
from frappe.utils import flt,cint, get_link_to_form
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
import json
from frappe import _
from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability
from frappe import _, bold

class OperationSequenceError(frappe.ValidationError):
	pass

class JC(JobCard):
    def on_update(self):
        self.validate_job_card_qty()
        self.validate_time_logs()
        self.set_status()
        self.validate_operation_id()
        self.validate_sequence_id()
        self.set_sub_operations()
        self.update_sub_operation_status()
        self.validate_work_order()
        self.update_work_order()
    def validate(self):
        if self.total_completed_qty > self.for_quantity:
            self.for_quantity = self.total_completed_qty

        self.validate_time_logs()
        self.set_status()
        self.validate_operation_id()
        self.validate_sequence_id()
        self.set_sub_operations()
        self.update_sub_operation_status()
        self.validate_work_order()
        self.update_work_order()
    def on_submit(self):
        if self.total_completed_qty > self.for_quantity:
            self.for_quantity = self.total_completed_qty
        self.validate_transfer_qty()
        self.validate_job_card()
        self.update_work_order()
        self.set_transferred_qty()
        if self.for_quantity > self.total_completed_qty:
            frappe.throw(_("Kindly Complete Planned Qty and Submit"))          
    
    def get_current_operation_data(self):
        return frappe.get_all(
            "Job Card",
            fields=[
                "sum(total_time_in_mins) as time_in_mins",
                "sum(total_completed_qty) as completed_qty",
                "sum(process_loss_qty) as process_loss_qty",
            ],
            filters={
                "docstatus": ("!=", 2),
                "work_order": self.work_order,
                "operation_id": self.operation_id,
                "is_corrective_job_card": 0,
            },
        )
    
    def validate_sequence_id(self):
       return
    def update_work_order(self):
        if not self.work_order:
            return

        if self.is_corrective_job_card and not cint(
            frappe.db.get_single_value(
                "Manufacturing Settings", "add_corrective_operation_cost_in_finished_good_valuation"
            )
        ):
            return

        for_quantity, time_in_mins, process_loss_qty = 0, 0, 0
        _from_time_list, _to_time_list = [], []

        data = self.get_current_operation_data()
        if data and len(data) > 0:
            for_quantity = flt(data[0].completed_qty)
            time_in_mins = flt(data[0].time_in_mins)
            if self.docstatus !=1:
                process_loss_qty = 0

        wo = frappe.get_doc("Work Order", self.work_order)

        if self.is_corrective_job_card:
            self.update_corrective_in_work_order(wo)

        self.validate_produced_quantity(for_quantity, process_loss_qty, wo)
        self.update_work_order_data(for_quantity, process_loss_qty, time_in_mins, wo)

@frappe.whitelist()
def make_time_log(args):
    if isinstance(args, str):
        args = json.loads(args)

    args = frappe._dict(args)
    doc = frappe.get_doc("Job Card", args.job_card_id)
    doc.validate_sequence_id()
    doc.add_time_log(args)
    wo = frappe.get_doc("Work Order",doc.work_order)
    if args.completed_qty and doc.sequence_id == len(wo.operations):
        current_qty = doc.total_completed_qty
        if len(wo.operations) !=1 and wo.operations[-2].completed_qty < current_qty:
            frappe.throw(_("Excess Production not allowed.Kindly Complete Previous Operations Qty before Completing Finished Good Qty"))
        se_dict =  make_stock_entry(doc.work_order,"Manufacture",args.completed_qty)

        se = frappe.get_doc(se_dict)
        se.insert(ignore_permissions=True)
        frappe.msgprint(
        msg="""
            <b>Stock Entry Created:</b><br>
            <a href="/app/stock-entry/{name}" target="_blank">{name}</a>
        """.format(name=se.name),
        title="Success",
        indicator="green"
        )
    else:
        if doc.sequence_id >1:
            prev_op = wo.operations[doc.sequence_id -2]
            if prev_op.completed_qty < doc.total_completed_qty:
                frappe.throw(_("Excess Production not allowed.Kindly Complete Previous Operations Qty before Completing this Operation Qty"))

@frappe.whitelist()
def get_mtfm_items(work_order):
    wo = frappe.get_doc("Work Order", work_order)
    items = []
    for row in wo.required_items:
        if row.transferred_qty and row.consumed_qty < row.transferred_qty:
            stock_status = get_stock_availability(row.item_code, wo.wip_warehouse)
            unconsumed_qty = row.transferred_qty - row.consumed_qty
            if stock_status[0] >= unconsumed_qty:
                items.append({
                    "item_code": row.item_code,
                    "allowed_qty": unconsumed_qty,
                    "s_warehouse": wo.wip_warehouse,
                    "t_warehouse": row.source_warehouse,
                    "uom": row.stock_uom,
                    "stock_uom": row.stock_uom,
                })
            else:
                items.append({
                    "item_code": row.item_code,
                    "allowed_qty": stock_status[0],
                    "s_warehouse": wo.wip_warehouse,
                    "t_warehouse": row.source_warehouse,
                    "uom": row.stock_uom,
                    "stock_uom": row.stock_uom,
                })

    return items

@frappe.whitelist()
def create_material_transfer(work_order, items, job_card ):
    items = frappe.parse_json(items)

    new_se = frappe.new_doc("Stock Entry")
    new_se.stock_entry_type = "Material Transfer"
    new_se.company = frappe.db.get_value("Work Order", work_order, "company")
    new_se.work_order = work_order
    new_se.posting_date = frappe.utils.today()
    new_se.custom_rm_job_card = job_card

    for row in items:
        if row['qty'] > row['allowed_qty']:
            frappe.throw(_(f"Excess Qty not allowed for {row['item_code']}"))
            return
        new_se.append("items", {
            "item_code": row["item_code"],
            "qty": row["qty"],
            "uom": row["uom"],
            "stock_uom": row["stock_uom"],
            "s_warehouse": row["s_warehouse"],
            "t_warehouse": row["t_warehouse"]
        })

    se = frappe.get_doc( new_se.as_dict())
    se.insert(ignore_permissions=True)
    frappe.msgprint(
    msg="""
        <b>Stock Entry Created:</b><br>
        <a href="/app/stock-entry/{name}" target="_blank">{name}</a>
    """.format(name=se.name),
    title="Success",
    indicator="green"
    )

@frappe.whitelist()
def force_submit_job_card(job_card):
    doc = frappe.get_doc("Job Card", job_card)
    doc.for_quantity = doc.total_completed_qty
    doc.save(ignore_permissions=True)
    doc.submit()
    return "Success"