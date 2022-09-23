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
    hold_state = fields.Selection(selection_add=[
        ('payment_hold', 'Payment Hold')])
    is_payment_bypassed = fields.Boolean('Is payment Bypassed?')
    is_payment_low = fields.Boolean('Is payment Low?')

    def write(self, vals):
        """
        if transaction amount is less than order amount mark it as payment_low.
        """

        res = super(SaleOrder, self).write(vals)
        if vals.get('order_line', False):
            payment_terms = self.env['account.payment.term'].search([('is_pre_payment', '=', True)])
            for order in self.filtered(lambda r: r.payment_term_id in payment_terms):
                if not order.is_payment_bypassed and order.state in ('sale', 'done'):# and not order.storage_contract:
                    txs = order.transaction_ids.filtered(lambda r: r.state in ('authorized', 'done'))
                    if txs:
                        amount = sum(txs.mapped('amount'))
                        if amount < order.amount_total:
                            transactions = order.transaction_ids.filtered(lambda r:r.state == 'authorized')
                            transactions.action_void()
                            order._action_cancel()
                            order.message_post(body='Cancel Reason : New line added Payment Hold')
                            order.action_draft()
                            order.hold_state = 'payment_hold'
                            order.is_payment_error = True
                            order.payment_warning = 'Payment Hold: Total Amount increased.Mismatch with Payment Transaction'

        return res

    def _action_cancel(self):
        res =  super(SaleOrder, self)._action_cancel()
        self.write({'is_payment_error': False})
        return res


    def action_confirm(self):
        self.ensure_one()
        credit_warning = ''#self.check_credit_limit()
        price_warning = ''#self.check_low_price()
        if self.payment_term_id.is_pre_payment and not self._context.get('bypass_payment'):
            if self.hold_state in ('release', 'payment_hold') or (not self.hold_state and not self.credit_warning and not self.low_price_warning):
                token = self.partner_id.get_authorize_token()
                error_msg = ''
                if not token:
                    error_msg = "There is no authorise.net token available in %s" % self.partner_id.display_name
                    self.write({'is_payment_error': True, 'payment_warning': error_msg, 'hold_state': 'payment_hold'})
                else:
                    self.write({'is_payment_error': False, 'payment_warning': "", 'hold_state': 'release'})
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
                        self.write({'is_payment_error': True, 'payment_warning': error_msg, 'hold_state': 'payment_hold'})
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
