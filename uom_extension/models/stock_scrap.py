# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(StockScrap, self)._onchange_product_id()
        self.product_uom_id = self.product_id.ppt_uom_id.id
