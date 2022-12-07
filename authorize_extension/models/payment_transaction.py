# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import re

from datetime import datetime
from dateutil import relativedelta

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.tools import float_compare
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

        authorize_API = AuthorizeAPI(self.acquirer_id)
        rounded_amount = round(self.amount, self.currency_id.decimal_places)
        invoices = self.invoice_ids.filtered(lambda r:r.state == 'posted' and r.payment_state in ('not_paid', 'partial'))
        if invoices:
            due_amount = round(sum(invoices.mapped('amount_residual')), self.currency_id.decimal_places)
            rounded_amount = min(rounded_amount, due_amount)
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
            else:
                raise ValidationError("Technical error contact administrator")
        elif self.env.context.get('from_invoice_reauth'):
            res_content = authorize_api.authorize_transaction_from_invoice(self, self.invoice_ids)
        else:
            res_content = authorize_api.authorize_transaction(self, self.sale_order_ids)
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

        if self.invoice_ids:
            self.invoice_ids.filtered(lambda inv: inv.state == 'draft').action_post()
            (payment.line_ids + self.invoice_ids.filtered(lambda rec: rec.state != 'cancel').line_ids).filtered(
                lambda line: line.account_id == payment.destination_account_id
                and not line.reconciled
            ).reconcile()

        return payment


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
        if status in ('settledSuccessfully', 'refundSettledSuccessfully', 'capturedPendingSettlement', 'refundPendingSettlement'):
            self.state = 'done'
            payment = self.payment_id
            if payment and payment.state == 'cancel':
                payment.action_draft()
                payment.action_post()
        elif status == 'authorizedPendingCapture':
            self.state = 'authorized'
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
        rounded_amount = round(amount_to_refund, refund_tx.currency_id.decimal_places)
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
