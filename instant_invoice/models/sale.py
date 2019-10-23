#-*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_quick_sale(self):
        for rec in self:
            rec.action_confirm()
            rec.picking_ids.action_confirm()
            rec.picking_ids.action_assign()
            for picking in rec.picking_ids:
                for move_line in picking.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            rec.picking_ids.button_validate()
            rec.picking_ids.deliver_products()
            rec.action_invoice_create()
            rec.invoice_ids.action_invoice_open()
        return True

    @api.multi
    def action_print_invoice(self):
        invoice = self.invoice_ids
        return invoice.invoice_print()

SaleOrder()
