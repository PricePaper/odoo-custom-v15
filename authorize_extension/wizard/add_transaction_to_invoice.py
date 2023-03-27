# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from ..authorize_request_custom import AuthorizeAPICustom
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round


class AddInvoiceTransaction(models.TransientModel):
    _name = "add.invoice.transaction"

    transaction_ref = fields.Char('Transaction ref')
    is_bank_tx = fields.Boolean('Is direct Bank Transaction')
    amount = fields.Float('Amount')
    move_id = fields.Many2one('account.move')
    transaction_fee_percentage = fields.Float('Transaction fee percentage')
    transaction_fee = fields.Float('Transaction Fee')
    add_transaction_fee = fields.Boolean('Add transaction fee?', default=True)
    amount_total = fields.Float('Total')

    # @api.onchange(amount)
    # def onchange_amount(self):

    @api.onchange('add_transaction_fee', 'amount')
    def onchange_transaction_fee(self):
        if self.add_transaction_fee:
            self.update(self._get_transaction_vals(self.amount))
        else:
            self.update({
                'transaction_fee_percentage': 0,
                'transaction_fee': 0,
                'amount_total': self.amount,
            })

    @api.model
    def default_get(self, fields):
        vals = super(AddInvoiceTransaction, self).default_get(fields)
        vals.update(self._get_transaction_vals())

        return vals

    def _get_transaction_vals(self, amount=0):
        vals = {}
        if self and self.move_id:
            move = self.move_id
        else:
            move = self.env['account.move'].browse(self._context.get('active_id'))
        partner = move.partner_id
        if not amount and move:
            vals.update({
                'move_id': self._context.get('active_id', False),
                'amount': move.amount_residual
            })
            amount = move.amount_residual
        if partner.property_card_fee > 0:
            amount_total = float_round(amount * ((100 + partner.property_card_fee) / 100), precision_digits=2)
            payment_fee = amount * (partner.property_card_fee / 100)
            vals.update({
                'transaction_fee_percentage': partner.property_card_fee,
                'transaction_fee': payment_fee,
                'amount_total': amount_total,
            })
        return vals

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
        payment_method_line = acquirer.journal_id.inbound_payment_method_line_ids \
            .filtered(lambda l: l.code == acquirer.provider)
        if p_type == 'outbound':
            payment_method_line = acquirer.journal_id.outbound_payment_method_line_ids \
                .filtered(lambda l: l.code == acquirer.provider)
        payment_values = {
            'amount': abs(self.amount_total),
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
        if self.transaction_fee:
            self.create_transaction_fee_move(tx_payment)
        invoice.filtered(lambda inv: inv.state == 'draft').action_post()
        (tx_payment.line_ids + invoice.filtered(lambda rec: rec.state != 'cancel').line_ids).filtered(
            lambda line: line.account_id == tx_payment.destination_account_id
                         and not line.reconciled
        ).reconcile()

        # auth transaction from card wsipe
        # else:
        #     authorize_api = AuthorizeAPICustom(acquirer[0])
        #     res_content = authorize_api.get_transaction_detail(self.transaction_ref)
        #
        #     if res_content.get('err_code', ''):
        #         raise ValidationError(_("Error: %s"%(res_content.get('err_msg', ''))))
        #     elif res_content.get('transaction', ''):
        #         invoice.an_transaction_ref = self.transaction_ref

    def create_transaction_fee_move(self, payment, to_reconcile=True):
        if self.transaction_fee:
            move = self.move_id
            journal = int(self.env['ir.config_parameter'].sudo().get_param('authorize_extension.transaction_fee_journal_id'))
            if not journal:
                raise ValidationError("Credit card transaction fee journal is not configured")
            account_receivable = move.partner_id and move.partner_id.property_account_receivable_id.id or False
            if not account_receivable:
                account_receivable = int(self.env['ir.property']._get('property_account_receivable_id', 'res.partner'))
            transaction_fee_account = int(self.env['ir.config_parameter'].sudo().get_param('authorize_extension.transaction_fee_account'))
            transaction_fee_move = self.env['account.move'].create({
                'move_type': 'entry',
                'company_id': move.company_id.id,
                'journal_id': journal,
                'ref': '%s - Transaction Fee' % move.name,
                'line_ids': [(0, 0, {
                    'account_id': account_receivable,
                    'company_currency_id': move.company_id.currency_id.id,
                    'credit': 0.0,
                    'debit': self.transaction_fee,
                    'journal_id': journal,
                    'name': '%s - Transaction Fee' % move.name,
                    'partner_id': move.partner_id.id
                }), (0, 0, {
                    'account_id': transaction_fee_account,
                    'company_currency_id': move.company_id.currency_id.id,
                    'credit': self.transaction_fee,
                    'debit': 0.0,
                    'journal_id': journal,
                    'name': '%s - Transaction Fee' % move.name,
                    'partner_id': move.partner_id.id
                })]
            })
            move.manual_fee_move_ids = [(4,transaction_fee_move.id)]
            transaction_fee_move.post()
            if to_reconcile:
                (payment.line_ids + transaction_fee_move.line_ids).filtered(
                    lambda line: line.account_id == payment.destination_account_id and not line.reconciled
                ).reconcile()
            return transaction_fee_move
