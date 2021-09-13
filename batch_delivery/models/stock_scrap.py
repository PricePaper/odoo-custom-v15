# -*- coding: utf-8 -*-

from odoo import api, fields, models, _



class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            move = self.mapped('picking_id').mapped('move_ids_without_package').filtered(lambda r: r.product_id == self.product_id)
            if move:
                self.product_uom_id = move.product_uom.id
            else:
                self.product_uom_id = self.product_id.uom_id.id
