# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from ..authorize_request_custom import AuthorizeAPICustom
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round


class ReauthInvoiceToken(models.TransientModel):
    _name = "reauth.invoice.token"

    token_id = fields.Many2one('payment.token', 'Payment Token')
    partner_id = fields.Many2one('res.partner', 'Customer')
    partner_shipping_id = fields.Many2one('res.partner', 'Shipping address')
    invoice_id = fields.Many2one('account.move', 'Shipping address')

    @api.model
    def default_get(self, default_fields):
        rec = super(ReauthInvoiceToken, self).default_get(default_fields)
        invoice = self.env['account.move'].browse(self._context.get('active_id'))
        sale = invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
        rec['invoice_id'] = invoice.id
        if sale:
            rec['partner_id'] = sale.partner_id.id
            rec['partner_shipping_id'] = sale.partner_shipping_id.id
        else:
            rec['partner_id'] = invoice.partner_id.id
            rec['partner_shipping_id'] = invoice.partner_id.id
        return rec

    def reautherize_invoice(self):

        self.ensure_one()
        invoice = self.invoice_id

        if invoice.is_authorize_tx_failed:
            token = self.token_id
            error_msg = ''
            if not token:
                error_msg = "There is no Token"
                invoice.write({'is_authorize_tx_failed': True})
            else:
                invoice.write({'is_authorize_tx_failed': False})
                reference = invoice.name
                count = self.env['payment.transaction'].sudo().search_count([('reference', 'ilike', invoice.name)])
                if count:
                    reference = '%s - %s' % (invoice.name, count)
                payment_fee = self.partner_id.property_card_fee
                amount = invoice.amount_residual
                if payment_fee:
                    amount = float_round(amount * ((100+payment_fee) / 100), precision_digits=2)
                    payment_fee = invoice.amount_residual * (payment_fee/100)
                tx_sudo = self.env['payment.transaction'].sudo().create({
                    'acquirer_id': token.acquirer_id.id,
                    'reference': reference,
                    'amount': amount,
                    'transaction_fee': payment_fee,
                    'currency_id': invoice.currency_id.id,
                    'partner_id': invoice.partner_id.id,
                    'token_id': token.id,
                    'operation': 'offline',
                    'tokenize': False,
                    'invoice_ids': [(4, invoice.id)]
                })

                tx_sudo.with_context({'from_authorize_custom': True, 'from_invoice_reauth': True})._send_payment_request()
                if tx_sudo.state == 'error':
                    error_msg = tx_sudo.state_message
                    invoice.write({'is_authorize_tx_failed': True})
            if error_msg:
                invoice.message_post(body=error_msg)
