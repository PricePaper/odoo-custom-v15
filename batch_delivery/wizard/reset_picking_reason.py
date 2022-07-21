# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderCancel(models.TransientModel):
    _name = 'reset.picking.reason'
    _description = "Reset Picking Reason"

    picking_id = fields.Many2one('stock.picking', string='Picking', required=True, ondelete='cascade')
    reason = fields.Text(string='Reason', required=1)

    def action_cancel(self):
        """
        post cancel reason in Picking and reset it.
        """
        self.picking_id.message_post(body='Cancel Reason : ' + self.reason)
        return self.picking_id.reset_picking()
