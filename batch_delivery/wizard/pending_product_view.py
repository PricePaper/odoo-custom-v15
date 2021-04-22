# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PendingProductView(models.TransientModel):
    _name = 'pending.product.view'
    _description = 'Pending Product View'


    batch_ids = fields.Many2many("stock.picking.batch")
    picking_ids = fields.Many2many('stock.picking')

    def generate_move_lines(self):
        """
        Extract the pickings from batch and filtered out the pending move lines.
        """

        records = self.batch_ids.mapped('picking_ids') if self.batch_ids else self.picking_ids
        move_lines = records.filtered(lambda pick: pick.state not in ['done', 'cancel']).mapped('move_lines').ids
        action = self.env['ir.actions.act_window'].for_xml_id('batch_delivery', 'stock_move_pending_product_action')
        action['domain'] = [('id', 'in', move_lines)]

        return action


PendingProductView()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
