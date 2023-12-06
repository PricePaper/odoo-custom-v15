# -*- coding: utf-8 -*-
# Part of Odoo. See ICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    to_refund = fields.Boolean(default=True)
    unit_price = fields.Float(string="Unit Price", copy=False)

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    _description = 'Return Picking'

    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        quantity = stock_move.product_qty
        price_unit = 0
        if stock_move.picking_id.picking_type_id.code == 'outgoing':
            price_unit = stock_move.price_unit
        elif stock_move.picking_id.picking_type_id.code == 'incoming':
            price_unit = -stock_move.price_unit

        for move in stock_move.move_dest_ids:
            if move.origin_returned_move_id and move.origin_returned_move_id != stock_move:
                continue
            if move.state in ('partially_available', 'assigned'):
                quantity -= sum(move.move_line_ids.mapped('product_qty'))
            elif move.state in ('done'):
                quantity -= move.product_qty
        quantity = float_round(stock_move.product_id.uom_id._compute_quantity(quantity,
                                                              stock_move.product_uom,
                                                              rounding_method='HALF-UP'),
                                precision_rounding=stock_move.product_id.uom_id.rounding)

        return {
            'product_id': stock_move.product_id.id,
            'quantity': quantity,
            'move_id': stock_move.id,
            'uom_id': stock_move.product_uom.id,
            'unit_price':price_unit
        }


    def _prepare_move_default_values(self, return_line, new_picking):

        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.move_id.product_uom.id,
            'price_unit':return_line.unit_price,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals
