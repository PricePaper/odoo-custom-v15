# -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_price = fields.Float(
        string='Cost', compute="_compute_purchase_price",
        digits='Product Price', store=True, readonly=True,
        groups="base.group_user")

    @api.depends('order_id.delivery_cost', 'product_id', 'company_id', 'currency_id', 'product_uom')
    def _compute_purchase_price(self):
        for line in self:
            if line.product_id:
                if line.is_delivery:
                    if line.order_id.carrier_id.delivery_type not in ['fixed', 'base_on_rule']:
                        line.purchase_price = line.working_cost
                    else:
                        line.purchase_price = line.order_id.carrier_id.average_company_cost
                elif line.storage_contract_line_id:
                    line.purchase_price = 0
                else:
                    if line.working_cost:
                        line.purchase_price = line.working_cost
                    else:
                        line.purchase_price = line.product_id.cost
            else:
                line.purchase_price = 0

    def wrapper_compute_po_price(self):
        for line in self:
            line._compute_purchase_price()
        return True
