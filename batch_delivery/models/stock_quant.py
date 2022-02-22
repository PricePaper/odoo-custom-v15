# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round



class StockQuant(models.Model):
    _inherit = 'stock.quant'

    quantity_onhand = fields.Float(compute='_compute_quantity_onhand_with_transit',string='Onhand Quantity')

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        product_id = self.product_id
        location_src = product_id and product_id.property_stock_location and \
                       product_id.property_stock_location.id or product_id and \
                       product_id.categ_id and product_id.categ_id.property_stock_location and \
                       product_id.categ_id.property_stock_location.id or False
        # if self.location_id:
        #     return
        if self.product_id.tracking in ['lot', 'serial']:
            previous_quants = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id.usage', 'in', ['internal', 'transit'])], limit=1, order='create_date desc')
            if previous_quants:
                self.location_id = previous_quants.location_id
        if not self.location_id:
            company_id = self.company_id and self.company_id.id or self.env.company.id
            if location_src and not product_id.qty_available:
                self.location_id = location_src
            else:
                self.location_id = self.env['stock.warehouse'].search(
                    [('company_id', '=', company_id)], limit=1).in_type_id.default_location_dest_id

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