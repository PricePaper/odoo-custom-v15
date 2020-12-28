# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_open_quants(self):
        return {}


ProductTemplate()


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

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.quantity_done',
                 'stock_move_ids.is_transit')
    def _compute_quantities(self):
        super(Product, self)._compute_quantities()
        for product in self:
            product_qty = 0
            for move in product.stock_move_ids.filtered(lambda rec: rec.is_transit and rec.state != 'cancel'):
                if move.product_uom.id != product.uom_id.id:
                    product_qty += move.product_uom._compute_quantity(move.quantity_done, product.uom_id,
                                                                      rounding_method='HALF-UP')
                else:
                    product_qty += move.quantity_done
            product.qty_available -= product_qty
            product.outgoing_qty -= product_qty
            product.transit_qty = product_qty


Product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
