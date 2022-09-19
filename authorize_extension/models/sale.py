# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import AccessError, UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_transaction_count(self):
        self.transaction_count = 0
        for order in self:
            order.transaction_count = len(order.transaction_ids)

    transaction_count = fields.Integer('Transaction count', compute=_get_transaction_count)
    is_payment_error = fields.Boolean('Is payment error?')
    payment_warning = fields.Text('Payment warning')
    credit_warning = fields.Text(string='Credit Limit Warning Message', compute='compute_credit_warning', copy=False)

    def action_confirm(self):
        self.ensure_one()
        credit_warning = ''#self.check_credit_limit()
        price_warning = ''#self.check_low_price()
        if self.payment_term_id.is_pre_payment and not self._context.get('bypass_payment'):
            if self.hold_state == 'release' or (not self.hold_state and not self.credit_warning and not self.low_price_warning):
                token = self.partner_id.get_authorize_token()
                error_msg = ''
                if not token:
                    error_msg = "There is no authorise.net token available in %s" % self.partner_id.display_name
                    self.write({'is_payment_error': True, 'payment_warning': error_msg})
                else:
                    self.write({'is_payment_error': False, 'payment_warning': ""})
                    reference = self.name
                    count = self.env['payment.transaction'].sudo().search_count([('reference', 'ilike', self.name)])
                    if count:
                        reference = '%s - %s' % (self.name, count)
                    tx_sudo = self.env['payment.transaction'].sudo().create({
                        'acquirer_id': token.acquirer_id.id,
                        'reference': reference,
                        'amount': self.amount_total,
                        'currency_id': self.currency_id.id,
                        'partner_id': self.partner_id.id,
                        'token_id': token.id,
                        'operation': 'offline',
                        'tokenize': False,
                        'sale_order_ids': [(4, self.id)]
                    })

                    tx_sudo.with_context({'from_authorize_custom': True})._send_payment_request()
                    if tx_sudo.state == 'error':
                        error_msg = tx_sudo.state_message
                        self.write({'is_payment_error': True, 'payment_warning': error_msg})
                if error_msg:
                    self.message_post(body=error_msg)
                    view_id = self.env.ref('price_paper.view_sale_warning_wizard').id
                    return {
                        'name': 'Warning',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'sale.warning.wizard',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'context': {'default_warning_message': error_msg},
                        'target': 'new'
                    }
        if self.is_payment_error and self._context.get('bypass_payment'):
            self.write({'is_payment_error': False})
            self.message_post(body='confirming without payment')
            return False
        return super(SaleOrder, self).action_confirm()

    def action_view_payment_transactions(self):
        action = self.env['ir.actions.act_window']._for_xml_id('payment.action_payment_transaction')

        if len(self.transaction_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.transaction_ids.id
            action['views'] = []
        else:
            action['domain'] = [('id', 'in', self.transaction_ids.ids)]

        return action

    def action_confirm_bypass(self):
        return self.action_confirm()

    def payment_action_capture_old(self):
        if not self.invoice_ids.filtered(lambda rec: rec.state != 'cancel'):
            action = self.env.ref('sale.action_view_sale_advance_payment_inv').read()[0]
            action.update({
                'context': {
                    'default_advance_payment_method': 'fixed',
                    'default_fixed_amount': self.amount_total,
                }
            })
            # return action
        invoice_to_paid = self.invoice_ids.filtered(lambda rec: rec.state != 'cancel' and rec.payment_state  == 'not_paid')
        if sum(invoice_to_paid.mapped('amount_total')) >= sum(self.authorized_transaction_ids.mapped('amount')):
            return super(SaleOrder, self.with_context({'create_payment': True})).payment_action_capture()
        raise ValidationError("authorised amount and invoiced amount is not matching\n please correct the invoice.")

SaleOrder()

