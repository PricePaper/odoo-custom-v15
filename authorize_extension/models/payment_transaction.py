# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import re

from datetime import datetime
from dateutil import relativedelta

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
from ..authorize_request_custom import AuthorizeAPICustom
from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI



_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):

    _name = 'payment.transaction'
    _inherit = ['payment.transaction', 'mail.thread']

    state = fields.Selection(
        string="Status",
        selection=[('draft', "Draft"), ('pending', "Pending"), ('authorized', "Authorized"),
                   ('done', "Confirmed"), ('cancel', "Canceled"), ('error', "Error")],
        default='draft', readonly=True, required=True, copy=False, index=True, tracking=True)
    acquirer_reference = fields.Char(
        string="Acquirer Reference", help="The acquirer reference of the transaction",
        readonly=True, tracking=True)
    amount = fields.Monetary(tracking=True)
    transaction_fee = fields.Float('Credit Card fee', tracking=True)
    transaction_fee_move_id = fields.Many2one('account.move', 'Credit Card fee move', ondelete="restrict", tracking=True)

    def _check_amount_and_confirm_order(self):
        self.ensure_one()
        if self.env.context.get('from_authorize_custom'):
            return
        return super(PaymentTransaction, self)._check_amount_and_confirm_order()

    def _send_capture_request(self):
        """ Override of payment to send a capture request to Authorize.

        Note: self.ensure_one()

        :return: None
        """
        self.ensure_one()
        if self.provider != 'authorize':
            return super()._send_capture_request()

        if self.state != 'authorized':
            raise ValidationError(_("Only authorized transactions can be captured."))

        authorize_API = AuthorizeAPI(self.acquirer_id)
        rounded_amount = round(self.amount, self.currency_id.decimal_places)

        invoices = self.invoice_ids.filtered(lambda r: r.state == 'posted' and r.payment_state in ('not_paid', 'partial'))
        if invoices:
            due_amount = round(sum(invoices.mapped('amount_residual')), self.currency_id.decimal_places)
            if self.transaction_fee:
                new_amount = min(round(rounded_amount-self.transaction_fee, 2), due_amount)
                if new_amount != round(rounded_amount-self.transaction_fee, 2):
                    self.transaction_fee = float_round(new_amount * self.partner_id.property_card_fee/100, precision_digits=2)
                due_amount += self.transaction_fee
            rounded_amount = round(min(rounded_amount, due_amount), self.currency_id.decimal_places)
        self.amount = rounded_amount

        res_content = authorize_API.capture(self.acquirer_reference, rounded_amount)
        # As the API has no redirection flow, we always know the reference of the transaction.
        # Still, we prefer to simulate the matching of the transaction by crafting dummy feedback
        # data in order to go through the centralized `_handle_feedback_data` method.
        feedback_data = {'reference': self.reference, 'response': res_content}
        self._handle_feedback_data('authorize', feedback_data)


    def action_capture(self):
        res = super(PaymentTransaction, self).action_capture()
        if self.state == 'done' and self._context.get('create_payment'):
            self.invoice_ids.filtered(lambda rec: rec.state == 'draft').action_post()
            self._create_payment()
        self.filtered(lambda rec: rec.state == 'done' and not rec.is_post_processed)._finalize_post_processing()
        if self.payment_id and self.state == 'done':
            self.send_receipt_mail()
        return res


    def _send_payment_request(self):
        """ Override of payment to send a payment request to Authorize extension custom module to add more values to Json and prevent printing information in logger.

        Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """

        if self.provider != 'authorize':
            return super()._send_payment_request()
        if not self.token_id.authorize_profile:
            raise UserError("Authorize.Net: " + _("The transaction is not linked to a token."))
        authorize_api = AuthorizeAPICustom(self.acquirer_id)
        if not self.acquirer_id.is_avs_check:
            authorize_api.avs_warning_check = False
        res_content = False
        if self.payment_id:
            if self._context.get('active_model') == 'account.move' and self._context.get('active_id'):
                invoice = self.env['account.move'].browse(self._context.get('active_id'))
                self.write({'invoice_ids': [(6, 0, [invoice.id])]})
                res_content = authorize_api.authorize_capture_transaction(self, invoice)
                invoice.write({'is_authorize_tx_failed': False})
                if res_content.get('x_response_reason_text') and not res_content.get('x_trans_id', False):
                    invoice.write({'is_authorize_tx_failed': True})
                    invoice.message_post(body=res_content.get('x_response_reason_text', ''))
            elif self._context.get('payments_need_tx'):
                res_content = authorize_api.authorize_capture_transaction(self, self.payment_id)
                # invoice.write({'is_authorize_tx_failed': False})
                if res_content.get('x_response_reason_text') and not res_content.get('x_trans_id', False):
                    # invoice.write({'is_authorize_tx_failed': True})
                    self.payment_id.message_post(body=res_content.get('x_response_reason_text', ''))
            else:
                raise ValidationError("Technical error contact administrator")
        elif self.env.context.get('from_invoice_reauth'):
            res_content = authorize_api.authorize_transaction_from_invoice(self, self.invoice_ids)
        else:
            res_content = authorize_api.authorize_transaction(self, self.sale_order_ids)
        if res_content.get('x_pending_avs_msg', ''):
            self.message_post(body='AVS Response: ' + res_content.get('x_pending_avs_msg', ''))
        feedback_data = {'reference': self.reference, 'response': res_content}
        self._handle_feedback_data('authorize', feedback_data)

    def _create_payment(self, **extra_create_values):
        """Create an `account.payment` record for the current transaction.

        If the transaction is linked to some invoices, their reconciliation is done automatically.

        Note: self.ensure_one()

        :param dict extra_create_values: Optional extra create values
        :return: The created payment
        :rtype: recordset of `account.payment`
        """
        self.ensure_one()

        payment_method_line = self.acquirer_id.journal_id.inbound_payment_method_line_ids\
            .filtered(lambda l: l.code == self.provider)
        payment_values = {
            'amount': abs(self.amount),  # A tx may have a negative amount, but a payment must >= 0
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            'journal_id': self.acquirer_id.journal_id.id,
            'company_id': self.acquirer_id.company_id.id,
            'payment_method_line_id': payment_method_line.id,
            'payment_token_id': self.token_id.id,
            'payment_transaction_id': self.id,
            'ref': self.reference,
            **extra_create_values,
        }
        payment = self.env['account.payment'].create(payment_values)
        payment.action_post()

        # Track the payment to make a one2one.
        self.payment_id = payment
        if self.transaction_fee:
            self.create_transaction_fee_move()
        if self.invoice_ids:
            self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
            (payment.line_ids + self.invoice_ids.filtered(lambda rec: rec.state != 'cancel').line_ids).filtered(
                lambda line: line.account_id == payment.destination_account_id
                and not line.reconciled
            ).reconcile()

        return payment

    def create_transaction_fee_move(self, to_reconcile=True):
        self.ensure_one()
        if self.transaction_fee and not self.transaction_fee_move_id:
            journal = int(self.env['ir.config_parameter'].sudo().get_param('authorize_extension.transaction_fee_journal_id'))
            if not journal:
                raise ValidationError("Credit Card fee journal is not configured")
            account_receivable = self.partner_id and self.partner_id.property_account_receivable_id.id or False
            if not account_receivable:
                account_receivable = int(self.env['ir.property']._get('property_account_receivable_id', 'res.partner'))
            transaction_fee_account = int(self.env['ir.config_parameter'].sudo().get_param('authorize_extension.transaction_fee_account'))
            transaction_fee_move = self.env['account.move'].create({
                'move_type': 'entry',
                'company_id': self.company_id.id,
                'journal_id': journal,
                'ref': '%s - Credit Card Fee' % self.reference,
                'line_ids': [(0, 0, {
                    'account_id': account_receivable,
                    'company_currency_id': self.company_id.currency_id.id,
                    'credit': 0.0,
                    'debit': self.transaction_fee,
                    'journal_id': journal,
                    'name': '%s - Credit Card Fee' % self.reference,
                    'partner_id': self.partner_id.id
                }), (0, 0, {
                    'account_id': transaction_fee_account,
                    'company_currency_id': self.company_id.currency_id.id,
                    'credit': self.transaction_fee,
                    'debit': 0.0,
                    'journal_id': journal,
                    'name': '%s - Credit Card Fee' % self.reference,
                    'partner_id': self.partner_id.id
                })]
            })
            self.transaction_fee_move_id = transaction_fee_move.id
            transaction_fee_move.action_post()
            if to_reconcile:
                (self.payment_id.line_ids + transaction_fee_move.line_ids).filtered(
                    lambda line: line.account_id == self.payment_id.destination_account_id and not line.reconciled
                ).reconcile()
            return transaction_fee_move


    def write_old(self, vals):
        if input(vals) == 'y':print(k)
        return super(PaymentTransaction, self).write(vals)

    def cron_check_pending_status(self):
        transactions = self.env['payment.transaction'].search([('state', '=', 'pending')])
        for tx in transactions:
            tx.check_pending_status()

    def check_pending_status(self):

        authorize_api = AuthorizeAPICustom(self.acquirer_id)
        res_content = authorize_api.get_transaction_detail(self.acquirer_reference)
        status = res_content.get('transaction', {}).get('transactionStatus', '')
        picking = self.sale_order_ids.picking_ids.filtered(lambda r: r.is_payment_hold)
        if status in ('settledSuccessfully', 'refundSettledSuccessfully', 'capturedPendingSettlement', 'refundPendingSettlement'):
            self.state = 'done'
            if picking:
                picking.write({'is_payment_hold': False})
                self.sale_order_ids.write({'is_transaction_pending': False, 'hold_state': 'release'})


            payment = self.payment_id
            if self.transaction_fee_move_id and self.transaction_fee_move_id.state == 'cancel':
                self.transaction_fee_move_id.button_draft()
                self.transaction_fee_move_id.action_post()
            if payment and payment.state == 'cancel':
                payment.action_draft()
                payment.action_post()
        elif status == 'authorizedPendingCapture':
            self.state = 'authorized'
            if self.sale_order_ids.filtered(lambda r: r.is_transaction_pending):
                self.sale_order_ids.filtered(lambda r: r.is_transaction_pending).write({'is_transaction_pending': False, 'hold_state': 'release'})
            if picking:
                picking.write({'is_payment_hold': False})

        elif status == 'voided':
            self.state = 'cancel'

    def action_refund(self, amount_to_refund=None):
        """ Check the state of the transactions and request their refund.
        :param float amount_to_refund: The amount to be refunded
        :return: None
        """

        if self.provider != 'authorize':
            return super().action_refund(amount_to_refund=amount_to_refund)

        if any(tx.state != 'done' for tx in self):
            raise ValidationError(_("Only confirmed transactions can be refunded."))

        authorize_api = AuthorizeAPICustom(self.acquirer_id)
        res_content = authorize_api.get_transaction_detail(self.acquirer_reference)
        status = res_content.get('transaction', {}).get('transactionStatus', '')
        if status in ('capturedPendingSettlement'):
            raise ValidationError(_("The selected transaction is not settled in API."))

        for tx in self:
            refund_tx = tx._send_refund_request(amount_to_refund)
            if refund_tx.state == 'done':
                refund_tx._create_payment()
                refund_tx.filtered(lambda rec: rec.state == 'done' and not rec.is_post_processed)._finalize_post_processing()

    def _send_refund_request(self, amount_to_refund=None, create_refund_transaction=True):
        """ Override of payment to send a refund request to Authorize.
        Note: self.ensure_one()
        :param float amount_to_refund: The amount to refund
        :param bool create_refund_transaction: Whether a refund transaction should be created or not
        :return: The refund transaction if any
        :rtype: recordset of `payment.transaction`
        """
        if self.provider != 'authorize':
            return super()._send_refund_request(
                amount_to_refund=amount_to_refund,
                create_refund_transaction=create_refund_transaction,
            )

        refund_tx = self._create_refund_transaction(amount_to_refund=amount_to_refund)
        refund_tx._log_sent_message()


        authorize_API = AuthorizeAPI(refund_tx.acquirer_id)
        rounded_amount = float_round(amount_to_refund, precision_digits=2)
        res_content = authorize_API.refund(self.acquirer_reference, rounded_amount)
        # As the API has no redirection flow, we always know the reference of the transaction.
        # Still, we prefer to simulate the matching of the transaction by crafting dummy feedback
        # data in order to go through the centralized `_handle_feedback_data` method.
        feedback_data = {'reference': refund_tx.reference, 'response': res_content}
        status_code = res_content.get('x_response_code', '3')
        if status_code == '1':  # Approved
            status_type = res_content.get('x_type').lower()
            if status_type in ('refund'):
                refund_tx._set_done()
                if refund_tx.tokenize and not self.token_id:
                    refund_tx._authorize_tokenize()
                refund_tx._execute_callback()
        refund_tx._handle_feedback_data('authorize', feedback_data)

        return refund_tx

    def _process_feedback_data(self, data):
        """ Override to fix acquirer_reference set as 0.
        """
        acquirer_reference = self.acquirer_reference
        res = super()._process_feedback_data(data)
        if self.provider == 'authorize' and self.acquirer_reference == '0':
            self.acquirer_reference = acquirer_reference
        return res

    def send_receipt_mail(self):
        mail_template1 = self.env.ref('authorize_extension.email_credit_card_fee_receipt')
        mail_template1.send_mail(self.payment_id.id, force_send=True)

    def check_error(self):
        return self.sudo().env.ref('authorize_extension.action_check_transaction_error').read()[0]
