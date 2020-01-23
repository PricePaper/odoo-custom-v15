# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def print_picking_operation(self):
        return self.env.ref('stock.action_report_picking').report_action(self, config=False)
