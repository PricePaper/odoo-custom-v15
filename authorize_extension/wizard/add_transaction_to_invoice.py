# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from ..authorize_request_custom import AuthorizeAPICustom
from odoo.exceptions import ValidationError


class AddInvoiceTransaction(models.TransientModel):
    _name = "add.invoice.transaction"

    transaction_ref = fields.Char('Transaction ref')
    is_bank_tx = fields.Boolean('Is direct Bank Transaction')
    amount = fields.Float('Amount')

    def add_transaction(self):
        invoice = self.env['account.move'].browse(self._context.get('active_id'))
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'authorize')])
        # if self.is_bank_tx:
        if self.amount < 0:
            raise ValidationError(_("Please Enter amount"))
        invoice.an_bank_tx_ref = self.transaction_ref
        if invoice.move_type == 'out_invoice':
            p_type = 'inbound'
        else:
            p_type = 'outbound'
        payment_method_line = acquirer.journal_id.inbound_payment_method_line_ids\
            .filtered(lambda l: l.code == acquirer.provider)
        if p_type == 'outbound':
            payment_method_line = acquirer.journal_id.outbound_payment_method_line_ids\
                .filtered(lambda l: l.code == acquirer.provider)
        payment_values = {
            'amount': abs(self.amount),
            'payment_type': p_type,
            'currency_id': acquirer.sudo().authorize_currency_id.id,
            'partner_id': invoice.partner_id.id,
            'partner_type': 'customer',
            'journal_id': acquirer.journal_id.id,
            'company_id': acquirer.company_id.id,
            'payment_method_line_id': payment_method_line.id,
            'ref': invoice.name + '-' + self.transaction_ref,
            'card_payment_type': 'bank'
            }
        tx_payment = self.env['account.payment'].create(payment_values)
        tx_payment.action_post()

        invoice.filtered(lambda inv: inv.state == 'draft').action_post()
        (tx_payment.line_ids + invoice.filtered(lambda rec: rec.state != 'cancel').line_ids).filtered(
            lambda line: line.account_id == tx_payment.destination_account_id
            and not line.reconciled
        ).reconcile()

        #auth transaction from card wsipe
        # else:
        #     authorize_api = AuthorizeAPICustom(acquirer[0])
        #     res_content = authorize_api.get_transaction_detail(self.transaction_ref)
        #
        #     if res_content.get('err_code', ''):
        #         raise ValidationError(_("Error: %s"%(res_content.get('err_msg', ''))))
        #     elif res_content.get('transaction', ''):
        #         invoice.an_transaction_ref = self.transaction_ref
