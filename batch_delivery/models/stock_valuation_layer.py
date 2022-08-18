# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.tools.float_utils import float_round


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    is_price_diff = fields.Boolean(string='Is price diff', compute='_compute_price_diff', search='_is_price_diff_search')

    def _compute_price_diff(self):

        for rec in self:
            if rec.remaining_qty > 0:
                svl_recs = rec.product_id.stock_valuation_layer_ids.filtered(lambda r: r.remaining_qty != 0)
                is_greater = True
                for svl_rec in svl_recs:
                    if svl_rec.create_date > rec.create_date:
                        is_greater = False
                        break
                if is_greater:
                    if float_round(rec.product_id.standard_price, 2) != float_round(rec.unit_cost, 2):
                        rec.is_price_diff = True
                    elif rec.product_id.seller_ids and float_round(rec.product_id.seller_ids[0].price, 2) != float_round(rec.unit_cost, 2):
                        rec.is_price_diff = True
                    else:
                        rec.is_price_diff = False
                else:
                    rec.is_price_diff = False
            else:
                rec.is_price_diff = False

    def _is_price_diff_search(self, operator, value):
        recs = self.search([]).filtered(lambda x : x.is_price_diff is True )
        if recs:
            return [('id', 'in', [x.id for x in recs])]
