# -*- coding: utf-8 -*-

from odoo import models, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        res = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        if self._context.get('from_purchase_write'):
            if 'price_unit' in res:
                res.remove('price_unit')
        return res
StockMove()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
