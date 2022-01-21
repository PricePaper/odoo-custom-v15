# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_arrival_date = fields.Datetime(string='Product Arrival Date', compute='compute_arrival_date')

    @api.depends('product_id')
    def compute_arrival_date(self):
        if self._context.get('partner_id'):
            for line in self:
                pass



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
