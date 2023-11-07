# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    def product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom or self.order_id.storage_contract:
            return {}
        if self.product_id.type == 'product' and self.is_mto is False:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.ppt_uom_id)
            if float_compare(product.quantity_available - product.outgoing_quantity, product_qty, precision_digits=precision) == -1:
                if not self.is_mto:
                    message = _('You plan to sell %.2f %s of %s but you only have %.2f %s available in %s warehouse.') % \
                              (self.product_uom_qty, self.product_uom.name, self.product_id.name,
                               product.quantity_available - product.outgoing_quantity, product.ppt_uom_id.name,
                               self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.quantity_available - product.outgoing_quantity,
                                     self.product_id.quantity_available - self.product_id.outgoing_quantity,
                                     precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available across all warehouses.\n\n') % \
                                   (self.product_id.quantity_available - self.product_id.outgoing_quantity, product.ppt_uom_id.name)
                        for warehouse in self.env['stock.warehouse'].search([]):
                            quantity = self.product_id.with_context(
                                warehouse=warehouse.id).quantity_available - self.product_id.with_context(
                                warehouse=warehouse.id).outgoing_quantity
                            if quantity > 0:
                                message += "%s: %s %s\n" % (warehouse.name, quantity, self.product_id.ppt_uom_id.name)
                    warning_mess = {
                        'title': 'Not enough inventory!',
                        'message': message
                    }
                    return {'warning': warning_mess}
        return {}

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
