# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Product(models.Model):
    _inherit = 'product.product'

    transit_qty = fields.Float("Transit Qty", compute='_compute_transit_quantities', store=True)

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.quantity_done')
    def _compute_transit_quantities(self):
        transit_location = self.env['stock.location'].search([('is_transit_location', '=', True)])
        qty_dict = self.with_context(location=transit_location.ids)._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.transit_qty = qty_dict[product.id]['qty_available']

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    @api.depends_context(
        'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
        'location', 'warehouse',
    )
    def _compute_quantities(self):
        super(Product, self)._compute_quantities()
        for product in self:
            product.outgoing_qty -= product.transit_qty

    def action_open_transit_moves(self):
        action = self.sudo().env.ref('stock.stock_move_action').read()[0]
        moves = self.stock_move_ids.filtered(lambda r: r.picking_id.is_transit and r.quantity_done > 0)
        action['domain'] = [('id', 'in', moves.ids)]
        action['context'] = {'search_default_groupby_location_id': 1}
        return action
        # transit_location = self.env['stock.location'].search([('is_transit_location', '=', True)])
        # res = self.with_context(location=transit_location.ids).action_open_quants()
        # return res

    def get_quantity_in_sale(self):
        self.ensure_one()
        moves = self.stock_move_ids.filtered(lambda move: move.sale_line_id and move.state not in ['cancel', 'done'] \
                                                          and not move.transit_picking_id and move.picking_code == 'outgoing' and move.picking_id.state not in ['cancel', 'done', 'in_transit'])
        sale_lines = moves.mapped('sale_line_id').ids

        action = self.sudo().env.ref('price_paper.act_product_2_sale_order_line').read()[0]
        action['domain'] = [('id', 'in', sale_lines)]
        return action

    def get_quantity_in_purchase(self):
        self.ensure_one()
        purchase_line_ids = self.stock_move_ids.filtered(lambda move: move.purchase_line_id and \
                                                                      move.state not in ['cancel', 'done']).mapped('purchase_line_id').ids
        action = self.sudo().env.ref('price_paper.act_res_partner_2_purchase_order_line').read()[0]
        action['domain'] = [('id', 'in', purchase_line_ids)]
        return action

    def _get_domain_locations_new(self, location_ids, company_id=False, compute_child=True):
        domain =  super()._get_domain_locations_new(location_ids, company_id, compute_child)
        if not self.env.context.get('location'):
            domain[0].append(('location_id.is_transit_location', '=', False))
        return domain

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
