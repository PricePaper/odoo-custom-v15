from odoo import fields, models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _update_received_qty(self):
        for line in self:
            total = 0.0
            # In case of a BOM in kit, the products delivered do not correspond to the products in
            # the PO. Therefore, we can skip them since they will be handled later on.
            for move in line.move_ids.filtered(lambda m: m.product_id == line.product_id):
                if move.state == 'done':
                    if move.location_dest_id.usage == "supplier":
                        if move.to_refund:
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    elif move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                        # Edge case: the dropship is returned to the stock, no to the supplier.
                        # In this case, the received quantity on the PO is set although we didn't
                        # receive the product physically in our stock. To avoid counting the
                        # quantity twice, we do nothing.
                        pass
                    else:
                        if move.rma_id and move.purchase_line_id:
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        else:
                            total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
            line.qty_received = total