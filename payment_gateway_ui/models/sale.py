# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.api import Environment
import odoo, time
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_is_zero
from datetime import datetime, timedelta, date
import logging


class SaleOrder(models.Model):
    _inherit = "sale.order"

    transaction_id = fields.Char('Transaction ID', copy=False)
    payment_id = fields.Char('Payment Profile ID', copy=False)
    transaction_date = fields.Datetime('Transaction Date', copy=False)
    refund = fields.Boolean('Refunded', copy=False)
    down_payment_amount = fields.Float(default=0.0, copy=False)
    gateway_type = fields.Selection([], string='Payment Gateway')

    @api.multi
    def resend_link(self):
        """
        resend the link if expired
        """
        for record in self:
            gateway_type = self.env['ir.config_parameter'].sudo().get_param('gateway_type')
            if not gateway_type:
                raise UserError(_('Warning ! \n Please check Payment Gateway configuration.'))
            Journal = self.env['account.journal'].search([('is_authorizenet', '=', True)], limit=1)
            if not Journal:
                raise UserError(_(
                'Error! \n Please Select The Authorize.net Journal.(Accounting->configuration->journal->Authorize.net Journal->True!'))
            self.env['payment.token.invoice'].edi_token_recreate(record, 'sale')
            print('inside resend')
            template_id = self.env.ref('payment_gateway_ui.email_template_sale_order_payment')
            print('template_id', template_id)
            if not template_id:
                raise UserError(_('Warning ! \n No Email Template found.'))
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
                default_model='sale.order',
                default_res_id=self.id,
                default_use_template=bool(template_id),
                default_template_id=template_id.id,
                default_composition_mode='comment',
                mark_invoice_as_sent=True,
            )
            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx,
            }
        return

    @api.multi
    def action_draft(self):
        for record in self:
            record.payment_id = False
            record.transaction_id = False
            record.transaction_date = False
            unlik_line = self.env['sale.order.line']
            for line in record.order_line:
                if line.product_id and line.product_id.id == int(
                        self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')):
                    unlik_line += line
            unlik_line.unlink()
        res = super(SaleOrder, self).action_draft()
        return res

    @api.multi
    def action_cancel(self):
        for record in self:
            record.down_payment_amount = 0
            for invoice in record.invoice_ids.filtered(lambda l: l.state != 'cancelled'):
                payment_record = self.env['payment.token.invoice'].search(
                    [('invoice_id', '=', invoice.id), ('model', '=', 'invoice')])
                payment_record.unlink()
                invoice.action_cancel()
        res = super(SaleOrder, self).action_cancel()
        return res

    @api.multi
    def action_reopen(self):
        """
        reset to quotation with payment fields False
        """
        for record in self:
            record.payment_id = False
            record.transaction_id = False
            record.transaction_id = False
            record.transaction_date = False
            unlik_line = self.env['sale.order.line']
            for line in record.order_line:
                if line.product_id and line.product_id.id == int(
                        self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')):
                    unlik_line += line
            unlik_line.unlink()

        res = super(SaleOrder, self).action_reopen()
        return res

    # Create down-payment or a full invoice based on the total amount
    @api.multi
    def create_down_payment(self, total_amount, handling_fee, invoice_total, paid_amount):
        for sale_order in self:
            sale_advance_vals = {
                'advance_payment_method': 'fixed',
                'amount': total_amount,
            }
            sale_advance = self.env['sale.advance.payment.inv'].create(sale_advance_vals)
            print('invoice_total', invoice_total)
            print('paramsssssssssss22222', total_amount + paid_amount + handling_fee)
            # print(test)
            if total_amount + paid_amount + handling_fee >= invoice_total:
                print('inside iffffffff')
                sale_advance.write({
                    'advance_payment_method': 'all',
                })
            if sale_advance.advance_payment_method == 'all':
                print('inside alll')
                invoice_id = sale_order.action_invoice_create(final=True)
                invoice = self.env['account.invoice'].browse(invoice_id)
                invoice.action_invoice_open()
                return invoice
            else:
                if not sale_advance.product_id:
                    vals = sale_advance._prepare_deposit_product()
                    sale_advance.product_id = sale_advance.env['product.product'].create(vals)
                    sale_advance.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id',
                                                                             sale_advance.product_id.id)
                sale_line_obj = self.env['sale.order.line']
                amount = sale_advance.amount
                if sale_advance.product_id.invoice_policy != 'order':
                    raise UserError(_(
                        'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if sale_advance.product_id.type != 'service':
                    raise UserError(_(
                        "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = sale_advance.product_id.taxes_id.filtered(
                    lambda r: not sale_order.company_id or r.company_id == sale_order.company_id)
                if sale_order.fiscal_position_id and taxes:
                    tax_ids = sale_order.fiscal_position_id.map_tax(taxes, sale_advance.product_id,
                                                                    sale_order.partner_shipping_id).ids
                else:
                    tax_ids = taxes.ids
                context = {'lang': sale_order.partner_id.lang}
                analytic_tag_ids = []
                for line in sale_order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': sale_order.id,
                    'discount': 0.0,
                    'product_uom': sale_advance.product_id.uom_id.id,
                    'product_id': sale_advance.product_id.id,
                    'analytic_tag_ids': analytic_tag_ids,
                    'tax_id': [(6, 0, tax_ids)],
                    'is_downpayment': True,
                })
                del context
                invoice = sale_advance._create_invoice(sale_order, so_line, amount)
                invoice.action_invoice_open()
                return invoice

    @api.multi
    def get_payment_url(self):
        """
        :return: Payment url
        """
        token = self.env['payment.token.invoice'].get_invoice_payment_record(self, 'sale')
        web_root_url = self.env['ir.config_parameter'].get_param('web.base.url')
        gateway_type = self.env['ir.config_parameter'].sudo().get_param('gateway_type')
        print('gateway_type', gateway_type)
        EDI_VIEW_WEB_URL = '%s/%s/payment?token=%s' % (web_root_url, gateway_type, token)
        return EDI_VIEW_WEB_URL

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for rec in self:
            if vals.get('order_line', False):
                product = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
                sale_line_deposit = rec.order_line.filtered(lambda line: line.product_id.id == int(product))
                order_line_ids = rec.order_line.filtered(lambda line: line.product_id.id != int(product))
                seq = 1
                for line in order_line_ids:
                    line.sequence = seq
                    seq += 1
                for line in sale_line_deposit:
                    line.sequence = seq
                    seq += 1
            if vals.get('payment_id', False):
                rec.partner_invoice_id and rec.partner_invoice_id.write({'payment_id': vals.get('payment_id', False)})
        return res

    @api.multi
    def copy(self, default=None):
        default = default or {}
        default.update({
            'user_id': self._uid,
        })
        res = super(SaleOrder, self).copy(default=default)
        unlink_line = self.env['sale.order.line']
        for line in res.order_line:
            if line.product_id and line.product_id.id == int(
                    self.env['ir.config_parameter'].get_param('sale.default_deposit_product_id')):
                unlink_line += line
        if unlink_line:
            unlink_line.unlink()
        return res


SaleOrder()
