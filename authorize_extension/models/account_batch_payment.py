# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date, datetime, timedelta
from ..authorize_request_custom import AuthorizeAPICustom


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    authorize_batch_ref = fields.Char('Authorize Batch Ref')

    def create_autherize_batch_payment(self):

        last_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        start_date = (datetime.now() - timedelta(1)).strftime("%Y-%m-%dT%H:%M:%S")

        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'authorize')])

        authorize_api = AuthorizeAPICustom(acquirer[0])
        res_content = authorize_api.get_batch(start_date, last_date)

        batches = res_content.get('batchList', [])
        payment_obj = self.env['account.payment']

        new_batch = self.env['account.batch.payment']

        for batch in batches:
            batch_id = batch.get('batchId', False)

            if batch_id:
                #if batch already exist then skip
                if self.env['account.batch.payment'].search([('authorize_batch_ref', '=', batch_id)]):
                    continue
                res_transactions = authorize_api.get_transaction_list(batch_id)
                transactions = res_transactions.get('transactions', [])
                payments_to_batch = self.env['account.payment']

                for transaction in transactions:
                    if transaction.get('transactionStatus', '') in ('settledSuccessfully', 'refundSettledSuccessfully'):
                        tx_ref = transaction.get('transId')
                        tx = self.env['payment.transaction'].search([('acquirer_reference', '=', tx_ref)])
                        #if transaction does not exist in odoo then create draft payment
                        if not tx:
                            invoice = self.env['account.move'].search([('an_transaction_ref', '=', tx_ref)])

                            amount = transaction.get('settleAmount', 0)
                            if transaction.get('transactionStatus', '') == 'settledSuccessfully':
                                p_type = 'inbound'
                            else:
                                p_type = 'outbound'
                            pay_profile = transaction.get('profile', {}).get('customerPaymentProfileId', '')
                            token = self.env['payment.token'].search([('acquirer_ref', '=', pay_profile)])
                            payment_method_line = acquirer.journal_id.inbound_payment_method_line_ids\
                                .filtered(lambda l: l.code == acquirer.provider)
                            if p_type == 'outbound':
                                payment_method_line = acquirer.journal_id.outbound_payment_method_line_ids\
                                    .filtered(lambda l: l.code == acquirer.provider)
                            #hard coded partner for credit card swipe transaction
                            partner = 1678
                            if token:
                                partner = token.partner_id.id
                            elif invoice:
                                partner = invoice.partner_id.id
                            payment_values = {
                                'amount': abs(amount),
                                'payment_type': p_type,
                                'currency_id': acquirer.authorize_currency_id.id,
                                'partner_id': partner,
                                'partner_type': 'customer',
                                'journal_id': acquirer.journal_id.id,
                                'company_id': acquirer.company_id.id,
                                'payment_method_line_id': payment_method_line.id,
                                'ref': transaction.get('invoiceNumber', '') + '-' + tx_ref,
                                'card_payment_type': 'authorize'
                                }
                            tx_payment = payment_obj.create(payment_values)
                            payments_to_batch |= tx_payment
                        else:
                            if tx.payment_id:
                                payments_to_batch |= tx.payment_id

                #add card swipe payments direct to the bank
                payment_last_date = fields.Date.today()
                payment_start_date = fields.Date.today() - timedelta(1)
                direct_bank_payments = payment_obj.search([('card_payment_type', '=', 'bank'),
                    ('batch_payment_id', '=', False),
                    ('date', '<=', payment_last_date),
                    ('date', '>=', payment_start_date)])
                if direct_bank_payments:
                    payments_to_batch |= direct_bank_payments

                #create batch for payments based on journal and payment method
                if payments_to_batch:
                    journals = payments_to_batch.mapped('journal_id')
                    payment_methods = payments_to_batch.mapped('payment_method_line_id')
                    for journal in journals:
                        for p_method in payment_methods:
                            filtered_payments = payments_to_batch.filtered(lambda r: r.journal_id == journal and r.payment_method_line_id == p_method)
                            if filtered_payments:
                                new_batch = self.env['account.batch.payment'].create({
                                    'journal_id': journal.id,
                                    'payment_method_line_id': p_method.id,
                                    'authorize_batch_ref': batch_id

                                    })
                                filtered_payments.write({'batch_payment_id': new_batch.id})
        if not new_batch:
            payment_last_date = fields.Date.today()
            payment_start_date = fields.Date.today() - timedelta(1)
            payments_to_batch = payment_obj.search([('card_payment_type', '=', 'bank'),
                ('batch_payment_id', '=', False),
                ('date', '<=', payment_last_date),
                ('date', '>=', payment_start_date)])
            if payments_to_batch:
                journals = payments_to_batch.mapped('journal_id')
                payment_methods = payments_to_batch.mapped('payment_method_line_id')
                for journal in journals:
                    for p_method in payment_methods:
                        filtered_payments = payments_to_batch.filtered(lambda r: r.journal_id == journal and r.payment_method_line_id == p_method)
                        if filtered_payments:
                            new_batch = self.env['account.batch.payment'].create({
                                'journal_id': journal.id,
                                'payment_method_line_id': p_method.id,
                                'authorize_batch_ref': batch_id

                                })
                            filtered_payments.write({'batch_payment_id': new_batch.id})




AccountBatchPayment()
