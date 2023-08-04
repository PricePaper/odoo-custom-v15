# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit='sale.order'

    is_sample_order = fields.Boolean(string='Sample Order',default=False)
    

    @api.model
    def create(self, vals):
        if vals.get('is_sample_order'):
            sequence = self.env.ref('sample_request.seq_sc_sale_order_sample', raise_if_not_found=False)
            if sequence:
                vals['name'] = sequence._next()
        order = super(SaleOrder, self).create(vals)
        return order



    def action_confirm(self):
        """
        create record in price history
        and also update the customer pricelist if needed.
        create invoice for bill_with_goods customers.

        """
        if self.is_sample_order:
            self = self.with_context(from_import=True)
        return super(SaleOrder, self).action_confirm()

class SaleOrderLine(models.Model):
    _inherit='sale.order.line'

    @api.depends('product_id', 'product_uom')
    def _compute_lst_cost_prices(self):
        super(SaleOrderLine,self)._compute_lst_cost_prices()
        for line in self:
            if line.order_id.is_sample_order:
                line.lst_price = 0.0

    @api.depends('product_id', 'product_uom_qty', 'price_unit', 'order_id.delivery_cost')
    def calculate_profit_margin(self):
        """
        Calculate profit margin for SO line
        """
        super(SaleOrderLine,self).calculate_profit_margin()
        for line in self:
            if line.order_id.is_sample_order:
                line.profit_margin = 0.0
  