# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('order_id.delivery_cost', 'product_id', 'company_id', 'currency_id', 'product_uom')
    def _compute_purchase_price(self):
        for line in self:
            if line.product_id:
                if line.is_delivery:
                    if self.order_id.carrier_id.delivery_type not in ['fixed', 'base_on_rule']:
                        line.purchase_price = line.working_cost
                    else:
                        line.purchase_price = line.order_id.carrier_id.average_company_cost
                else:
                    if line.working_cost:
                        line.purchase_price = line.working_cost
                    else:
                        line.purchase_price = line.product_id.cost
            else:
                line.purchase_price = 0
