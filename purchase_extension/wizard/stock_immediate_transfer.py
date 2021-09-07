# See LICENSE file for full copyright and licensing details.

from odoo import api, models

class StockOverProcessedTransfer(models.TransientModel):
    _inherit = 'stock.overprocessed.transfer'

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        if self.picking_id.purchase_id:
            self.picking_id.purchase_id.write({'state': 'received'})
        return super(StockOverProcessedTransfer, self).action_confirm()

class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    @api.multi
    def process(self):
        res = super(StockImmediateTransfer, self).process()
        self.pick_ids.mapped('purchase_id').write({'state': 'received'})
        return res
