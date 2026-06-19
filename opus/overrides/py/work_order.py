import frappe
from frappe import _
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from frappe.utils import flt

class CustomWO(WorkOrder):
    def update_operation_status(self):
        allowance_percentage = flt(
            frappe.db.get_single_value("Manufacturing Settings", "overproduction_percentage_for_work_order")
        )
        max_allowed_qty_for_wo = flt(self.qty) + (allowance_percentage / 100 * flt(self.qty))

        for d in self.get("operations"):
            precision = d.precision("completed_qty")
            qty = flt(flt(d.completed_qty, precision) + flt(d.process_loss_qty, precision), precision)
            if not qty:
                d.status = "Pending"
            elif qty < flt(self.qty, precision):
                d.status = "Work in Progress"
            else:
                d.status = "Completed"
