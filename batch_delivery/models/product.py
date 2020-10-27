# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Product(models.Model):
    _inherit = 'product.template'

    def action_open_quants(self):
        return {}


class Product(models.Model):
    _inherit = 'product.product'

    transit_qty = fields.Float("Transit Qty", compute='_compute_quantities', store=True)

    def action_open_quants(self):
        return {}

    def action_open_transit_moves(self):
        action = self.env.ref('stock.stock_move_action').read()[0]
        action['domain'] = [('id', 'in', self.stock_move_ids.ids), ('is_transit', '=', True), ('quantity_done', '>', 0)]
        action['context'] = {'search_default_groupby_location_id': 1}
        return action

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.quantity_done', 'stock_move_ids.is_transit')
    def _compute_quantities(self):
        super(Product, self)._compute_quantities()
        for product in self:
            quant = sum(product.stock_move_ids.filtered(lambda rec: rec.is_transit and rec.state != 'cancel').mapped(
                'quantity_done'))
            product.qty_available -= quant
            product.outgoing_qty -= quant
            product.transit_qty = quant or 0
