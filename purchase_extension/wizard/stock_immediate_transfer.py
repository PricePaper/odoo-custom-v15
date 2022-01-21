# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'


    def process(self):
        res = super(StockImmediateTransfer, self).process()
        self.pick_ids.mapped('purchase_id').write({'state': 'received'})
        return res
