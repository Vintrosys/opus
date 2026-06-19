import frappe
from frappe import _
from frappe.utils import flt
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry, FinishedGoodError

class CustomSe(StockEntry):
    def validate_work_order(self):
        if self.purpose == "Manufacture" and self.work_order:
            jc = frappe.get_list("Job Card", filters={"work_order": self.work_order, "status":"Open"})
            if jc:
                frappe.throw(_("Please complete the Job card before completing Manufacture Stock entry."))
        if self.purpose in (
            "Manufacture",
            "Material Transfer for Manufacture",
            "Material Consumption for Manufacture",
            "Disassemble",
        ):
            # check if work order is entered

            if (
                self.purpose == "Manufacture" or self.purpose == "Material Consumption for Manufacture"
            ) and self.work_order:
                if not self.fg_completed_qty:
                    frappe.throw(_("For Quantity (Manufactured Qty) is mandatory"))
                self.check_duplicate_entry_for_work_order()
        elif self.purpose != "Material Transfer":
            self.work_order = None

    def validate_finished_goods(self):
        production_item, wo_qty, finished_items = None, 0, []
        if self.work_order:
            wo_details = frappe.db.get_value("Work Order", self.work_order, ["production_item", "qty"])
            if wo_details:
                production_item, wo_qty = wo_details

        for d in self.get("items"):
            if d.is_finished_item:
                if not self.work_order:
                    finished_items.append(d.item_code)
                    continue

                if d.item_code != production_item:
                    frappe.throw(
                        _("Finished Item {0} does not match with Work Order {1}").format(
                            d.item_code, self.work_order
                        )
                    )

                finished_items.append(d.item_code)

        if not finished_items:
            frappe.throw(
                msg=_("There must be atleast 1 Finished Good in this Stock Entry").format(self.name),
                title=_("Missing Finished Good"),
                exc=FinishedGoodError,
            )

        if self.purpose == "Manufacture":
            if len(set(finished_items)) > 1:
                frappe.throw(
                    msg=_("Multiple items cannot be marked as finished item"),
                    title=_("Note"),
                    exc=FinishedGoodError,
                )
            
            # Bypassed overproduction validation here