# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    quick_sale = fields.Boolean(string='is_quick_sale', default=False, copy=False)

    # Note V15 following odoo's default Delivery method logic by Add Shipping button

    def compute_credit_warning_old(self):
        for order in self:
            if not order.quick_sale and order.carrier_id:
                order.adjust_delivery_line()
        return super(SaleOrder, self).compute_credit_warning()

    def write(self, vals):
        """
        auto save the delivery line.
        """
        # for order in self:
        #     if vals.get('state', '') == 'done' and not order.state == 'done':
        #         if not order.quick_sale and order.carrier_id:
        #             order.adjust_delivery_line()
        #         else:
        #             order._remove_delivery_line()
        res = super(SaleOrder, self).write(vals)
        if self._context.get('action_cancel'):
            return res
        for order in self:
            if order.state != 'done' and ('state' not in vals or vals.get('state', '') != 'done') and not self._context.get('action_confrim'):
                if not order.quick_sale and order.carrier_id:
                    order.adjust_delivery_line()
                # else:
                #     order._remove_delivery_line()
        return res

    def action_quick_sale(self):

        for rec in self.sudo():
            if all(line.product_id.type == 'service' for line in rec.order_line):
                raise Warning("You cannot confirm a quick Sales Order with only having Service products.")
            rec.quick_sale = True
            if not rec.quick_sale:
                if not any(order_lines.is_delivery for order_lines in rec.order_line):
                    raise ValidationError('Delivery lines should be added in order lines before confirming an order')
            res = rec.action_confirm()
            if res and res != True and res.get('context') and res.get('context').get('warning_message'):
                return res
            picking_ids = rec.picking_ids.filtered(lambda r: r.state not in ('cancel', 'done', 'in_transit'))
            for picking in picking_ids:
                picking.action_assign_transit()
                picking.receive_product_in_lines()
                picking.action_make_transit()
                picking.create_invoice()
                invoice = picking.invoice_ids
                invoice.write({'invoice_date': fields.Date.today()})
        return True

    def action_print_pick_ticket(self):
        picking = self.picking_ids
        return picking.print_picking_operation()

    def action_print_product_label(self):
        picking = self.picking_ids
        return picking.print_product_label()

    def action_print_invoice(self):
        invoice = self.invoice_ids
        invoice.sudo().filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})
        return self.env.ref('instant_invoice.account_invoices_quick_sale').report_action(invoice)

    def print_quotation(self):
        if self.quick_sale:
            return self.env.ref('instant_invoice.action_report_quick_saleorder') \
                .with_context(discard_logo_check=True).report_action(self)
        return super(SaleOrder, self).print_quotation()

    def action_release_credit_hold(self):
        """
        release hold sale order for credit limit exceed.
        """
        for order in self:
            order.write({'is_creditexceed': False, 'ready_to_release': True})
            order.message_post(body="Credit Team Approved")
            if order.release_price_hold or not order.check_low_price():
                order.hold_state = 'release'
                if not self.quick_sale:
                    order.action_confirm()
                else:
                    order.action_quick_sale()
            else:
                order.hold_state = 'price_hold'

    def action_release_price_hold(self):
        """
        release hold sale order for low price.
        """
        for order in self:
            order.write({'is_low_price': False, 'release_price_hold': True})
            order.message_post(body="Sale Team Approved")
            if order.ready_to_release or not order.check_credit_limit():
                order.hold_state = 'release'
                if not self.quick_sale:
                    order.action_confirm()
                else:
                    order.action_quick_sale()
            else:
                order.hold_state = 'credit_hold'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
