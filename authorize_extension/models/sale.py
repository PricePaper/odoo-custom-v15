# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_round


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_transaction_count(self):
        self.transaction_count = 0
        for order in self:
            order.transaction_count = len(order.transaction_ids)

    transaction_count = fields.Integer('Transaction count', compute=_get_transaction_count)
    is_payment_error = fields.Boolean('Is payment error?', copy=False)
    payment_warning = fields.Text('Payment warning', copy=False)
    credit_warning = fields.Text(string='Credit Limit Warning Message', compute='compute_credit_warning', copy=False)
    hold_state = fields.Selection(selection_add=[
        ('payment_hold', 'Payment Hold')])
    is_payment_bypassed = fields.Boolean('Is payment Bypassed?', copy=False)
    is_payment_low = fields.Boolean('Is payment Low?', copy=False)
    token_id = fields.Many2one('payment.token', 'Payment Token')
    is_pre_payment = fields.Boolean('Is prepayment?', related='payment_term_id.is_pre_payment')


    @api.onchange('partner_shipping_id', 'payment_term_id')
    def onchange_partner_payment_term(self):

        token = False
        if self.partner_shipping_id and self.partner_id and self.payment_term_id.is_pre_payment:
            default_parent_token = False
            parent_token = self.partner_id.payment_token_ids.filtered(lambda r: not r.shipping_id)
            if len(parent_token) == 1:
                default_parent_token = parent_token
            elif len(parent_token) > 1:
                default_parent_token = parent_token.filtered(lambda r: r.is_default)

            if self.partner_shipping_id == self.partner_id:
                token = default_parent_token
            else:
                shipping_token = self.partner_shipping_id.shipping_payment_token_ids
                if len(shipping_token) == 1:
                    token = shipping_token
                elif len(shipping_token) > 1:
                    token = shipping_token.filtered(lambda r: r.is_default)
                else:
                    token = default_parent_token
            if token:
                token.id

        self.token_id = token


    def action_payment_hold(self, error_msg='', cancel_reason=''):
        self.ensure_one()
        if self.state not in ('drfat', 'sent'):
            self._action_cancel()
            self.action_draft()
            self.message_post(body=cancel_reason)
        self.write({
            'hold_state': 'payment_hold',
            'is_payment_error': True,
            'payment_warning': error_msg
        })

    def write(self, vals):
        """
        if transaction amount is less than order amount mark it as payment_low.
        """

        res = super(SaleOrder, self).write(vals)
        if vals.get('order_line', False):
            payment_terms = self.env['account.payment.term'].search([('is_pre_payment', '=', True)])
            for order in self.filtered(lambda r: r.payment_term_id in payment_terms):
                if not order.is_payment_bypassed and order.state in ('sale', 'done'):  # and not order.storage_contract:
                    txs = order.transaction_ids.filtered(lambda r: r.state in ('authorized', 'done'))
                    if txs:
                        amount = sum(txs.mapped('amount'))
                        if amount < order.amount_total:
                            transactions = order.transaction_ids.filtered(lambda r: r.state == 'authorized')
                            transactions.action_void()
                            order.action_payment_hold('Payment Hold: Total Amount increased.Mismatch with Payment Transaction',
                                                      'Cancel Reason : New line added Payment Hold')
        if 'payment_term_id' in vals.keys():
            for order in self:
                if not order.payment_term_id.is_pre_payment and order.is_payment_error:
                    self.write({'is_payment_error': False, 'payment_warning': "", 'hold_state': 'release'})
        return res

    def _action_cancel(self):
        res = super(SaleOrder, self)._action_cancel()
        self.write({'is_payment_error': False})
        if self.mapped('transaction_ids').filtered(lambda r: r.state == 'done'):
            raise ValidationError("Transaction/s is/are already captured.")
        txs = self.mapped('transaction_ids').filtered(lambda r: r.state == 'authorized')
        txs.action_void()

        return res

    def action_confirm(self):
        self.ensure_one()
        res = super(SaleOrder, self).action_confirm()
        if isinstance(res, dict):
            return res

        if self.state in ('sale', 'done') and self.payment_term_id.is_pre_payment and not self._context.get('bypass_payment') and self.amount_total > 0:
            # token = self.partner_shipping_id.get_authorize_token() or self.partner_id.get_authorize_token()
            valid_transaction  = self.transaction_ids.filtered(lambda rec: rec.state in ('pending', 'authorized', 'done'))
            if self.amount_total <= sum(valid_transaction.mapped('amount')):
                self.message_post(body="Odoo prevents a duplicate authorize transaction request.\n please contact administrator immediately.")
                return res
            error_msg = ''
            if not self.token_id:
                error_msg = "Payment Token Not selected."
                self.action_payment_hold(error_msg, "Payment Token Not selected.")
            else:
                self.write({'is_payment_error': False, 'payment_warning': "", 'hold_state': 'release'})
                reference = self.name
                count = self.env['payment.transaction'].sudo().search_count([('reference', 'ilike', self.name)])
                if count:
                    reference = '%s - %s' % (self.name, count)
                payment_fee = self.partner_id.property_card_fee
                amount = self.amount_total
                if payment_fee:
                    amount = float_round(self.amount_total * ((100+payment_fee) / 100), precision_digits=2)
                    payment_fee = self.amount_total * (payment_fee/100)
                tx_sudo = self.env['payment.transaction'].sudo().create({
                    'acquirer_id': self.token_id.acquirer_id.id,
                    'reference': reference,
                    'amount': amount,
                    'transaction_fee': payment_fee,
                    'currency_id': self.currency_id.id,
                    'partner_id': self.partner_id.id,
                    'token_id': self.token_id.id,
                    'operation': 'offline',
                    'tokenize': False,
                    'sale_order_ids': [(4, self.id)]
                })

                tx_sudo.with_context({'from_authorize_custom': True})._send_payment_request()
                if tx_sudo.state == 'error':
                    error_msg = tx_sudo.state_message
                    self.action_payment_hold(error_msg, "no payment token available in customer")
                if tx_sudo.state == 'cancel':
                    error_msg = "The transaction with reference %s for %s is canceled (Authorize.Net)." % (tx_sudo.reference, tx_sudo.amount)
                    self.action_payment_hold(error_msg, error_msg)
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
            self.write({'is_payment_bypassed': False})
        if self.is_payment_error and self._context.get('bypass_payment'):
            self.write({'is_payment_error': False, 'hold_state': 'release', 'is_payment_bypassed': True})
            self.message_post(body='confirming without payment')
        return res

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
        invoice_to_paid = self.invoice_ids.filtered(lambda rec: rec.state != 'cancel' and rec.payment_state == 'not_paid')
        if sum(invoice_to_paid.mapped('amount_total')) >= sum(self.authorized_transaction_ids.mapped('amount')):
            return super(SaleOrder, self.with_context({'create_payment': True})).payment_action_capture()
        raise ValidationError("authorised amount and invoiced amount is not matching\n please correct the invoice.")


SaleOrder()
