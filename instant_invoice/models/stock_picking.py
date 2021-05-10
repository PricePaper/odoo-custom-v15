# -*- coding: utf-8 -*-

from odoo import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def print_picking_operation(self):
        return self.env.ref('instant_invoice.quick_sale_batch_picking_active_report').report_action(self, config=False)

    @api.multi
    def print_product_label(self):
        return self.env.ref('instant_invoice.quick_sale_product_label_report').report_action(self, config=False)

StockPicking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
