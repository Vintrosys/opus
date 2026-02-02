import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


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