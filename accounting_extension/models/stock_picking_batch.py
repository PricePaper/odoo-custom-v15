# -*- coding: utf-8 -*-

from odoo import models
from odoo.exceptions import UserError


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    def add_new_partner_line(self):
        """
        Return 'add cash collected line wizard'
        """
        self.ensure_one()
        if self.state not in ('no_payment', 'paid', 'cancel'):
            return {
                'name': 'New Customer Payment',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'add.cash.collected.wizard',
                'view_id': self.env.ref('accounting_extension.view_cash_collected_wizard').id,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            raise UserError("Cannot add payment to this batch")
