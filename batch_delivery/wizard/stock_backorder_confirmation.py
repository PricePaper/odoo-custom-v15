# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    reason = fields.Text('Reason for Returning')

    @api.one
    def _process(self, cancel_backorder=False):
        StockReturn = self.env['stock.picking.return']
        for pick_id in self.pick_ids:
            StockReturn.create({
                'name': 'RETURN-' + pick_id.name,
                'reason': self.reason,
                'picking_id': pick_id.id,
                'sale_id': pick_id.sale_id.id,
                'sales_person_ids': [
                    (6, 0, pick_id.sale_id and
                     pick_id.sale_id.sales_person_ids and
                     pick_id.sale_id.sales_person_ids.ids)],
                'return_line_ids': [(0, 0, {
                    'product_id': move.product_id.id,
                    'ordered_qty': move.product_uom_qty,
                    'delivered_qty': move.quantity_done if move.reserved_availability == move.product_uom_qty else move.reserved_availability,
                }) for move in pick_id.move_ids_without_package if move.quantity_done != move.product_uom_qty]
            })
            order = self.env['sale.order.line'].search(
                [('order_id', '=', pick_id.sale_id.id), ('is_delivery', '=', True)])
            order.write({'product_uom_qty': order.product_uom_qty + 1})
        super(StockBackorderConfirmation, self)._process(cancel_backorder)
