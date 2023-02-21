# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    price_per_unit = fields.Monetary('Cost Per Unit', compute='compute_price_per_unit')

    def compute_price_per_unit(self):
        for line in self:
            line.price_per_unit = line.final_cost / line.quantity
