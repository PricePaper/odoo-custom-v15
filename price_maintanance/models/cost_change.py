# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class CostChange(models.Model):
    _inherit = 'cost.change'



    @api.model
    def default_get(self, fields_list):
        res = super(CostChange, self).default_get(fields_list)
        if self._context.get('product_id', False):
            res['product_id'] = self._context.get('product_id')
        return res


    @api.model
    def standard_price_cron(self):
        """
        cron to update standard price
        """

        today = datetime.now()
        start_date = today - relativedelta(days=60)
        products = self.env['product.product'].search([('type', '=', 'product')])
        orders = self.env['sale.order'].search([('state', 'in', ['sale', 'done']), ('confirmation_date', '>=', start_date),('confirmation_date', '<=', today)])
        order_lines = self.env['sale.order.line']
        for order in orders:
            order_lines |= order.order_line
        for product in products:
            sale_order_lines_60_day_back = order_lines.filtered(lambda line: line.product_id.id == product.id and line.order_id.confirmation_date >= start_date)

            partner_lines = {}
            for line in sale_order_lines_60_day_back:
                if line.order_id.partner_id.id not in partner_lines:
                    partner_lines[line.order_id.partner_id.id] = {line.product_uom.id: line.price_unit}
                else:
                    if line.product_uom.id not in partner_lines[line.order_id.partner_id.id]:
                        partner_lines[line.order_id.partner_id.id][line.product_uom.id] = line.price_unit





CostChange()
