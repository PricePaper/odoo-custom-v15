# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockOverProcessedTransfer(models.TransientModel):
    _inherit = 'stock.overprocessed.transfer'


    @api.multi
    def action_confirm(self):
        self.ensure_one()
        for move in self.picking_id.move_ids_without_package:
            if move.is_storage_contract and move.purchase_line_id:
                if move.po_original_qty < move.quantity_done:
                    self.picking_id.over_processed = True
                    move.purchase_line_id.order_id.message_post(body='processed more than what was initially planned for the product %s'%move.product_id.display_name)

        return super(StockOverProcessedTransfer, self).action_confirm()

class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    @api.multi
    def process(self):
        res = super(StockImmediateTransfer, self).process()
        storage_contract = self.pick_ids.mapped('purchase_id').mapped('order_line.sale_order_id').filtered(
            lambda s: s.storage_contract)
        storage_contract.write({'state': 'received'})
        return res
