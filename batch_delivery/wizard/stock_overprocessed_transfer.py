# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockOverProcessedTransfer(models.TransientModel):
    _name = 'stock.overprocessed.transfer'
    _description = 'Transfer Over Processed Stock'

    picking_id = fields.Many2one('stock.picking')
    overprocessed_product_name = fields.Char(compute='_compute_overprocessed_product_name',
                                             readonly=True)

    def _compute_overprocessed_product_name(self):
        for wizard in self:
            moves = wizard.picking_id._get_overprocessed_stock_moves()
            wizard.overprocessed_product_name = moves[0].product_id.display_name

    def action_confirm(self):
        self.ensure_one()
        so = self.env['sale.order']
        for move in self.picking_id.move_ids_without_package:
            if move.is_storage_contract and move.purchase_line_id:
                if move.po_original_qty < move.quantity_done:
                    move.purchase_line_id.order_id.message_post(
                        body='processed more than what was initially planned for the product %s' % move.product_id.display_name)
                so |= move.purchase_line_id.order_id.mapped('order_line.sale_order_id')
        if so:
            so.write({'state': 'received'})
        return self.picking_id.with_context(skip_overprocessed_check=True).button_validate()
