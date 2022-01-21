# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Product(models.Model):
    _inherit = 'product.product'

    transit_qty = fields.Float("Transit Qty", compute='_compute_quantities', store=True)

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.quantity_done',
                 'stock_move_ids.is_transit')
    def _compute_quantities(self):
        res = super(Product, self)._compute_quantities()
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
        return res

    def action_open_transit_moves(self):
        action = self.env.ref('stock.stock_move_action').read()[0]
        moves = self.stock_move_ids.filtered(lambda r: r.is_transit and r.quantity_done > 0)
        action['domain'] = [('id', 'in', moves.ids)]
        action['context'] = {'search_default_groupby_location_id': 1}
        return action

    def get_quantity_in_sale(self):
        self.ensure_one()
        moves = self.stock_move_ids.filtered(
            lambda move: move.sale_line_id and move.state not in ['cancel',
                                                                  'done'] and not move.is_transit and move.picking_code == 'outgoing')

        moves |= self.stock_move_ids.filtered(
            lambda move: move.sale_line_id and move.state not in ['cancel',
                                                                  'done'] and move.is_transit and move.product_uom_qty != move.quantity_done)
        sale_lines = moves.mapped('sale_line_id').ids

        action = self.env.ref('price_paper.act_product_2_sale_order_line').read()[0]
        action['domain'] = [('id', 'in', sale_lines)]
        return action

    def get_quantity_in_purchase(self):
        self.ensure_one()
        purchase_line_ids = self.stock_move_ids.filtered(
            lambda move: move.purchase_line_id and move.state not in ['cancel', 'done']).mapped('purchase_line_id').ids
        action = self.env.ref('price_paper.act_res_partner_2_purchase_order_line').read()[0]
        action['domain'] = [('id', 'in', purchase_line_ids)]
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
