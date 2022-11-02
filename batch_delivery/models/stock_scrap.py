# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    reverse_move_id = fields.Many2one('stock.move', 'Reverse Move', readonly=True, copy=False)

    def action_reverse(self):

        move = self.move_id
        vals = {
            'name': self.name,
            'origin': self.name,
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'state': 'draft',
            'product_uom_qty': self.scrap_qty,
            'location_id': self.scrap_location_id.id,
            'location_dest_id': self.location_id.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                           'product_uom_id': self.product_uom_id.id,
                                           'qty_done': self.scrap_qty,
                                           'location_id': self.scrap_location_id.id,
                                           'location_dest_id': self.location_id.id,
                                           'package_id': self.package_id.id,
                                           'owner_id': self.owner_id.id,
                                           'lot_id': self.lot_id.id, })],
            # 'picking_id': self.picking_id.id
        }
        reverse_move = self.env['stock.move'].create(vals)
        reverse_move.with_context(is_scrap=True)._action_done()
        self.write({'reverse_move_id': reverse_move.id})
        return True

    def action_get_reverse_stock_move_lines(self):
        action = self.env['ir.actions.act_window']._for_xml_id('stock.stock_move_line_action')
        action['domain'] = [('move_id', '=', self.reverse_move_id.id)]
        return action
