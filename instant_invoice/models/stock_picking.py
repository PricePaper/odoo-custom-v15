# -*- coding: utf-8 -*-

from odoo import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def print_picking_operation(self):
        return self.env.ref('stock.action_report_picking').report_action(self, config=False)

    @api.multi
    def print_product_label(self):
        return self.env.ref('batch_delivery.product_label_report').report_action(self, config=False)

StockPicking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
