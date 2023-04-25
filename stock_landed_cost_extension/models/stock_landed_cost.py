# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    vendor_bill_ids = fields.Many2many(comodel_name='account.move', relation='account_move_stock_landed_cost_rel',
                                       column1='landed_cost_id', column2='vendor_bill_id')
