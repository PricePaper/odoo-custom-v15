# -*- coding: utf-8 -*-


from odoo import fields, models, tools
from odoo.tools import float_compare, float_is_zero


class StockValuationLayer(models.Model):
    """Stock Valuation Layer inherit"""

    _inherit = 'stock.valuation.layer'

    # changing related field to ppt_uom_id
    uom_id = fields.Many2one(related='product_id.ppt_uom_id', readonly=True, required=True)