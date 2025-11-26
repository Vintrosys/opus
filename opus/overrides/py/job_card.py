from erpnext.manufacturing.doctype.job_card.job_card import JobCard
import frappe
from frappe.utils import flt,cint
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
import json

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
        self.validate_time_logs()
        self.set_status()
        self.validate_operation_id()
        self.validate_sequence_id()
        self.set_sub_operations()
        self.update_sub_operation_status()
        self.validate_work_order()
        self.update_work_order()
    
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
    if args.completed_qty:
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

@frappe.whitelist()
def get_mtfm_items(work_order):
    mtfm = frappe.get_list(
        "Stock Entry",
        filters={
            "work_order": work_order,
            "stock_entry_type": "Material Transfer for Manufacture",
            "docstatus": ["!=", 2]
        },
        order_by="creation desc",
        limit=1
    )

    if not mtfm:
        return []

    doc = frappe.get_doc("Stock Entry", mtfm[0].name)

    items = []
    for row in doc.items:
        if not row.is_finished_item:  # only RM
            items.append({
                "item_code": row.item_code,
                "qty": row.qty,
                "uom": row.uom,
                "stock_uom": row.stock_uom,
                "conversion_factor": row.conversion_factor,
                "s_warehouse": row.t_warehouse or doc.to_warehouse,
                "t_warehouse": row.s_warehouse,
                "serial_and_batch_bundle": row.serial_and_batch_bundle
            })

    return items

@frappe.whitelist()
def create_material_transfer(work_order, items):
    items = frappe.parse_json(items)

    new_se = frappe.new_doc("Stock Entry")
    new_se.stock_entry_type = "Material Transfer"
    new_se.company = frappe.db.get_value("Work Order", work_order, "company")
    new_se.work_order = work_order
    new_se.posting_date = frappe.utils.today()

    print(items)

    for row in items:
        new_se.append("items", {
            "item_code": row["item_code"],
            "qty": row["qty"],
            "uom": row["uom"],
            "stock_uom": row["stock_uom"],
            "conversion_factor": row["conversion_factor"],
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