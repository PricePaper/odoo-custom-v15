# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def _process(self, cancel_backorder=False):
        so = self.env['sale.order']
        for pick_id in self.pick_ids:
            for move in pick_id.move_ids_without_package:
                if move.is_storage_contract and move.purchase_line_id:
                    so |= move.purchase_line_id.order_id
                    move.purchase_line_id.order_id.message_post(
                        body='processed less than what was initially planned for the product %s' % move.product_id.display_name)
        if so:
            so.write({'state': 'received'})

        super(StockBackorderConfirmation, self)._process(cancel_backorder)


StockBackorderConfirmation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
