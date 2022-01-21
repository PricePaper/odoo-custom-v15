# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResetQuantity(models.TransientModel):
    _name = 'stock.reset.quantity'
    _description = "Stock picking reset quantity"

    qty_update = fields.Float(string='Quantity to update')

    def action_reset(self):
        return self.env['stock.move'].browse(self._context.get('active_ids', [])).action_reset(qty=self.qty_update)


ResetQuantity()
