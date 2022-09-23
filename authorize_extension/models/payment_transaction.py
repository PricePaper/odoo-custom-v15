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



_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _check_amount_and_confirm_order(self):
        self.ensure_one()
        if self.env.context.get('from_authorize_custom'):
            return
        return super(PaymentTransaction, self)._check_amount_and_confirm_order()

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
        res_content = False
        if self.env.context.get('from_invoice_reauth'):
            res_content = authorize_api.authorize_transaction(self, self.sale_order_ids)
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
