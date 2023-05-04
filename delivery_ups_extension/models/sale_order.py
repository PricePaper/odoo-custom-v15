# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('move_ids', 'move_ids.stock_valuation_layer_ids', 'move_ids.picking_id.state', 'order_id.delivery_cost', 'product_id', 'company_id', 'currency_id', 'product_uom')
    def _compute_purchase_price(self):
        res = super(SaleOrderLine, self)._compute_purchase_price()
        for line in self:
            if line.is_delivery:
                if self.order_id.carrier_id.delivery_type not in ['fixed', 'base_on_rule']:
                    line.purchase_price = line.working_cost
                else:
                    line.purchase_price = line.order_id.carrier_id.average_company_cost
        return res
