# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
    def _compute_theoretical_qty(self):
        if not self.product_id:
            self.theoretical_qty = 0
            return
        theoretical_qty = self.product_id.get_theoretical_quantity(
            self.product_id.id,
            self.location_id.id,
            lot_id=self.prod_lot_id.id,
            package_id=self.package_id.id,
            owner_id=self.partner_id.id,
            to_uom=self.product_uom_id.id,
        )
        product_qty = 0
        for move in self.product_id.stock_move_ids.filtered(lambda rec: rec.is_transit and rec.state != 'cancel' and rec.location_id == self.location_id):
            if move.product_uom.id != self.product_id.uom_id.id:
                product_qty += move.product_uom._compute_quantity(move.quantity_done, self.product_id.uom_id,
                                                                  rounding_method='HALF-UP')
            else:
                product_qty += move.quantity_done
        if product_qty:
            product_qty = self.product_id.uom_id._compute_quantity(product_qty, self.product_uom_id)
        self.theoretical_qty = theoretical_qty - product_qty

    @api.onchange('product_id')
    def _onchange_theoretical_qty(self):
        self.product_qty = self.theoretical_qty
