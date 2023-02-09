# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api


class StockValuationLayer(models.Model):
    """Stock Valuation Layer"""

    _inherit = 'stock.valuation.layer'

    @api.model
    @api.returns('self',
                 upgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else self.browse(value),
                 downgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else value.ids)
    def search(self, args, offset=0, limit=None, order=None, count=False):

        res = super().search(args, offset=offset, limit=limit, order=order, count=count)
        res = self.browse(res) if count else res
        if self.env.context.get('storage_contract', False):
            for move in self.env.context.get('storage_contract', []):
                if move.sale_line_id and move.sale_line_id.storage_contract_line_id:
                    sale_line = move.sale_line_id.with_context({'storage_contract': False, 'action_done': False})
                    res = sale_line.storage_contract_line_id.move_ids.stock_valuation_layer_ids
                    return res if not count else res.ids
        elif self.env.context.get('action_done'):
            svl = self.env['stock.valuation.layer']
            for record in res:
                if not record.stock_move_id.is_storage_contract:
                    svl |= record
            res = svl
        return res if not count else res.ids


StockValuationLayer()

