# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    quick_sale = fields.Boolean(string='is_quick_sale', default=False, copy=False)

    def action_quick_sale(self):
        for rec in self.sudo():
            if all(line.product_id.type == 'service' for line in rec.order_line):
                raise Warning("You cannot confirm a quick Sales Order with only having Service products.")
            rec.quick_sale = True
            res = rec.action_confirm()
            if res and res != True and res.get('context') and res.get('context').get('warning_message'):
                return res
            picking_ids = rec.picking_ids.filtered(lambda r: r.state not in ('cancel', 'done', 'in_transit'))
            for picking in picking_ids:
                picking.action_make_transit()
                picking.create_invoice()
            # rec.quick_sale = True
        return True

    def action_print_pick_ticket(self):
        picking = self.picking_ids
        return picking.print_picking_operation()

    def action_print_product_label(self):
        picking = self.picking_ids
        return picking.print_product_label()


    def action_print_invoice(self):
        invoice = self.invoice_ids
        invoice.filtered(lambda inv: not inv.sent).write({'sent': True})
        return self.env.ref('instant_invoice.account_invoices_quick_sale').report_action(invoice)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
