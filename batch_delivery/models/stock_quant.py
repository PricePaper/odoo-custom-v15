# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round



class StockQuant(models.Model):
    _inherit = 'stock.quant'

    quantity_onhand = fields.Float(compute='_compute_quantity_onhand_with_transit')


    def _compute_quantity_onhand_with_transit(self):
        for rec in self:
            product_qty = 0
            for move in rec.product_id.stock_move_ids.filtered(lambda r: r.is_transit and r.location_id.id == rec.location_id.id and r.state != 'cancel'):
                if move.product_uom.id != rec.product_id.uom_id.id:
                    product_qty += move.product_uom._compute_quantity(move.quantity_done, rec.product_id.uom_id, rounding_method='HALF-UP')
                else:
                    product_qty += move.quantity_done
            rec.quantity_onhand = rec.quantity - product_qty

# todo don't know the usage
    # @api.model
    # def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
    #                               strict=False):
    #     pass