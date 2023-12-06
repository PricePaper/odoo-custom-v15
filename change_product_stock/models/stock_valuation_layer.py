# -*- coding: utf-8 -*-


from odoo import fields, models, tools
from odoo.tools import float_compare, float_is_zero


class StockValuationLayer(models.Model):
    """Stock Valuation Layer inherit"""

    _inherit = 'stock.valuation.layer'


    def name_get(self):
        result = []
        if self._context.get('from_change_stock_move', False):
            for move in self:
                result.append((move.id, 'Qty-%s  Cost-%s Date-%s' % (move.remaining_qty, move.unit_cost, move.create_date)))
            return result
        return super().name_get()
