#-*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    quick_sale = fields.Boolean(string='is_quick_sale', default=False, copy=False)

    @api.multi
    def write(self, vals):
        """
        auto save the delivery line.
        """
        res = super(SaleOrder, self).write(vals)
        for order in self:
            if order.quick_sale:
                order._remove_delivery_line()

    @api.multi
    def action_quick_sale(self):
        for rec in self:
            rec.quick_sale = True
            rec.action_confirm()
            rec.picking_ids.action_confirm()
            rec.picking_ids.action_assign()
            rec.picking_ids.button_validate()
            rec.action_invoice_create()
            rec.invoice_ids.action_invoice_open()
            # rec.quick_sale = True
        return True

    @api.multi
    def action_print_invoice(self):
        invoice = self.invoice_ids
        return invoice.invoice_print()

    @api.multi
    def action_print_picking_operation(self):
        picking = self.picking_ids
        return picking.print_picking_operation()

    @api.multi
    def action_print_product_label(self):
        picking = self.picking_ids
        return picking.print_product_label()


SaleOrder()
