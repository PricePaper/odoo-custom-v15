# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process_cancel_backorder(self):
        make2order_moves = self.env['stock.move']
        for picking in self.pick_ids:
            if picking.sale_id:
                picking.check_return_reason()

                if not picking.is_return and picking.picking_type_code == 'outgoing':
                    self.env['stock.picking.return'].create({
                        'name': 'RETURN-' + picking.name,
                        'picking_id': picking.id,
                        'sale_id': picking.sale_id.id,
                        'sales_person_ids': [
                            (6, 0, picking.sale_id and
                             picking.sale_id.sales_person_ids and
                             picking.sale_id.sales_person_ids.ids)],
                        'return_line_ids': [(0, 0, {
                            'product_id': move.product_id.id,
                            'ordered_qty': move.product_uom_qty,
                            'delivered_qty': move.quantity_done,
                            'reason_id': move.reason_id.id
                        }) for move in picking.move_lines if move.quantity_done != move.product_uom_qty]
                    })
                for move in picking.move_lines:
                    if move.quantity_done <= 0 and move.procure_method == 'make_to_order' and not move.location_id.is_transit_location:
                        make2order_moves |= move
                        print('make2order\'***************', move.location_id.name, move.location_id.is_transit_location)
                        continue
        skip_backorder = self.pick_ids
                    # move.sale_line_id.pre_delivered_qty += move.quantity_done
        if make2order_moves:
            self = self.with_context(skip_backorder=False)
            self.backorder_confirmation_line_ids.filtered(
                lambda rec: rec.picking_id in make2order_moves.mapped('picking_id')).write({'to_backorder': True})
            skip_backorder = skip_backorder-make2order_moves.mapped('picking_id')
        self = self.with_context(picking_ids_not_to_backorder=skip_backorder.ids)
        super(StockBackorderConfirmation, self).process()
        if make2order_moves:
            move_lines = self.pick_ids.mapped('backorder_ids').mapped('move_lines')
            (move_lines - make2order_moves)._action_cancel()
            for move in make2order_moves:
                move.move_orig_ids.write({'transit_picking_id': move.picking_id.id})


StockBackorderConfirmation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
