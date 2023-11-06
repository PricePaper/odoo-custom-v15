# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id.volume', 'product_id.weight')
    def _compute_gross_weight_volume(self):
        for line in self:
            product_qty = line.product_id.uom_id._compute_quantity(line.product_qty,
                                                                   line.product_id.ppt_uom_id or line.product_id.uom_id)
            line.gross_volume = line.product_id.volume * product_qty
            line.gross_weight = line.product_id.weight * product_qty

    @api.depends('product_id.qty_available', 'product_id.outgoing_qty')
    def compute_available_qty(self):
        for line in self:
            if line.product_id:
                line.product_onhand = line.product_id.quantity_available - line.product_id.outgoing_quantity
            else:
                line.product_onhand = 0.00