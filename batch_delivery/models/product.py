# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

class Product(models.Model):
    _inherit = 'product.product'

    transit_qty = fields.Float("Transit Qty", compute='_compute_transit_quantities', store=True)
    last_inventoried_date = fields.Date(string="Last Inventoried Date")
    in_qty = fields.Float("IN Qty", compute='_compute_in_out_quantities', digits='Product Unit of Measure')
    out_qty = fields.Float("OUT Qty", compute='_compute_in_out_quantities', digits='Product Unit of Measure')


    def action_inventory_history(self):
        self.ensure_one()
        action = {
            'name': _('History'),
            'view_mode': 'list,form',
            'res_model': 'stock.move.line',
            'views': [(self.env.ref('stock.view_move_line_tree').id, 'list'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'context': {
                'search_default_inventory': 1,
                'search_default_done': 1,
            },
            'domain': [
                ('product_id', '=', self.id),
                '|',
                    ('location_id', '=', self.property_stock_location.id),
                    ('location_dest_id', '=', self.property_stock_location.id),
            ],
        }
        return action


    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.quantity_done')
    def _compute_in_out_quantities(self):
        for product in self:
            # purchase_moves = product.stock_move_ids.filtered(lambda move: move.purchase_line_id and \
            #                                                               move.state not in ['cancel', 'done'])
            purchase_moves = self.env['stock.move'].search([('product_id', '=', product.id),
                ('picking_code', '=', 'incoming'), ('state', 'not in', ('cancel', 'done')),
                ('picking_id.is_return', '=', False),
                ('picking_id.rma_id', '=', False)])
            sale_moves = self.env['stock.move'].search([('product_id', '=', product.id),
                ('picking_code', '=', 'outgoing'), ('state', 'not in', ('cancel', 'done')),
                ('picking_id.is_return', '=', False),
                ('picking_id.state', 'not in', ('in_transit', 'cancel', 'done', 'transit_confirmed')),
                ('picking_id.rma_id', '=', False)])
            product_qty = 0
            for move in purchase_moves:
                product_qty += move.product_qty
            product.in_qty = product_qty
            product_qty = 0
            for move in sale_moves:
                product_qty += move.product_qty
            product.out_qty = product_qty



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
        moves = self.stock_move_ids.filtered(lambda r: (r.transit_picking_id.is_transit or r.transit_picking_id.is_transit_confirmed) and r.quantity_done > 0 and r.transit_picking_id.state != 'cancel')
        action['domain'] = [('id', 'in', moves.ids)]
        action['context'] = {'search_default_groupby_location_id': 1}
        return action
        # transit_location = self.env['stock.location'].search([('is_transit_location', '=', True)])
        # res = self.with_context(location=transit_location.ids).action_open_quants()
        # return res

    def get_quantity_in_sale(self):
        self.ensure_one()
        moves = self.stock_move_ids.filtered(lambda move: move.sale_line_id and move.state not in ['cancel', 'done'] \
                                                          and not move.transit_picking_id and move.picking_code == 'outgoing' and move.picking_id.state not in ['cancel', 'done','in_transit', 'transit_confirmed'])
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
