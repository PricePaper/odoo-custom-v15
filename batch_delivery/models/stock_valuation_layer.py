# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.tools.float_utils import float_round


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    is_price_diff = fields.Boolean(string='Is price diff', compute='_compute_price_diff', search='_is_price_diff_search')
    product_price = fields.Float(sting='Product Cost', digits='Product Price', related='product_id.standard_price')
    seller_price = fields.Float(sting='Seller Price', digits='Product Price', compute='_compute_seller')
    seller_id = fields.Many2one('res.partner', sting='Seller', compute='_compute_seller')

    def _compute_seller(self):
        for rec in self:
            if rec.product_id.seller_ids:
                seller = rec.product_id.seller_ids[0].name
                rec.seller_id = seller.id
                rec.seller_price = rec.product_id.seller_ids[0].price
            else:
                rec.seller_id = False
                rec.seller_price = 0

    def _compute_price_diff(self):

        for rec in self:
            if rec.remaining_qty > 0:
                if rec.stock_move_id and rec.stock_move_id.picking_id and rec.stock_move_id.picking_id.rma_id:
                    rec.is_price_diff = False
                else:
                    svl_recs = rec.product_id.stock_valuation_layer_ids.filtered(lambda r: r.remaining_qty != 0 and r.create_date > rec.create_date)
                    is_greater = True
                    for svl_rec in svl_recs:
                        if svl_rec.stock_move_id and svl_rec.stock_move_id.picking_id and svl_rec.stock_move_id.picking_id.rma_id:
                            continue
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
