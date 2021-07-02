# -*- coding: utf-8 -*-

from odoo import models, api, _

class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'


    @api.multi
    def add_new_partner_line(self):
        """
        Return 'add cash collected line wizard'
        """
        view_id = self.env.ref('accounting_extension.view_cash_collected_wizard').id

        return {
            'name': _('Add Cash Collected Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.cash.collected.wizard',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

StockPickingBatch()
