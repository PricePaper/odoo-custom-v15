# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_authorize_tx_failed = fields.Boolean('Authorize.net Transaction Failed')
    an_transaction_ref = fields.Char('Authorize.net Transaction')
    an_bank_tx_ref = fields.Char('Card Transaction Ref')
    transaction_fee = fields.Monetary(
        string="Credit Card Fee",
        compute='_compute_transaction_fee'
    )
    transaction_fee_manual = fields.Float("Credit Card Fee manual")
    manual_fee_move_ids = fields.Many2many(
        comodel_name='account.move',
        relation='account_move_transaction_fee_rel',
        column1='move_id',
        column2='transaction_fee_id',
        string='Manual payment fee moves')

    def calculate_gross_profit(self):
        """
        Compute the gross profit in invoice.
        """
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                move.gross_profit = 0
                continue
            if move.payment_state in ('paid', 'in_payment'):
                gross_profit = 0
                for line in move.invoice_line_ids:
                    gross_profit += line.profit_margin
                fee = 0
                for partial, amount, counterpart_line in move._get_reconciled_invoices_partials():
                    payment_method = counterpart_line.payment_id.payment_method_line_id.payment_method_id
                    if payment_method.payment_fee != 0.0:
                        fee += amount * (payment_method.payment_fee / 100)
                if fee:
                    gross_profit -= fee
                transaction_fee = 0
                if move.transaction_fee:
                    gross_profit += move.transaction_fee
                discount = move.get_discount()
                if discount:
                    gross_profit -= discount
                if move.move_type == 'out_refund':
                    if gross_profit < 0:
                        gross_profit = 0
                move.update({'gross_profit': round(gross_profit, 2)})

            else:
                gross_profit = 0
                for line in move.invoice_line_ids:
                    gross_profit += line.profit_margin
                if move.invoice_payment_term_id.discount_per > 0:
                    gross_profit -= move.amount_total * (move.invoice_payment_term_id.discount_per / 100)
                if move.move_type == 'out_refund':
                    if gross_profit < 0:
                        gross_profit = 0
                move.update({'gross_profit': round(gross_profit, 2)})

    @api.depends('transaction_ids')
    def _compute_transaction_fee(self):
        """
        Sum all the Credit Card fee amount for which state
        is in 'authorized' or 'done'
        """
        for invoice in self:
            invoice.transaction_fee = 0
            fee = 0
            if invoice.transaction_ids.filtered(
                    lambda tx: tx.state in ('authorized', 'done')):
                fee = sum(
                    invoice.transaction_ids.filtered(
                        lambda tx: tx.state in ('authorized', 'done')
                    ).mapped('transaction_fee')
                )
            if invoice.transaction_fee_manual:
                fee += invoice.transaction_fee_manual
            if fee:
                invoice.transaction_fee = fee

    def get_transaction_fee(self):
        self.ensure_one()
        return float_round(self.amount_total * (self.partner_id.property_card_fee / 100) or 0, precision_digits=2)

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft)
        for move in self.filtered(lambda r: r.move_type in ('out_refund', 'out_invoice')):
            if move.filtered(lambda r: r.invoice_date_due <= fields.Date.today()).mapped('authorized_transaction_ids').filtered(lambda r: r.state in ('authorized')):
                move.with_context({'create_payment': True}).payment_action_capture()
        return res


    def add_transaction_to_invoice(self):
        return self.sudo().env.ref('authorize_extension.action_add_transaction_to_invoice').read()[0]

    def action_register_payment(self):

        if self.mapped('authorized_transaction_ids').filtered(lambda r: r.state in ('authorized', 'done')):
            raise ValidationError(_("Selected Invoice(s) have/has authorized or confirmed transaction."))
        return super(AccountMove, self).action_register_payment()


    def action_reautherize_transaction(self):

        return self.sudo().env.ref('authorize_extension.action_invoice_reauthorize_wizard').read()[0]

    def payment_action_capture(self):
        self.ensure_one()
        valid_transaction = self.transaction_ids.filtered(lambda rec: rec.state in ('pending', 'authorized', 'done'))
        if len(valid_transaction) > 1 and self.amount_total <= sum(valid_transaction.mapped('amount')):
            raise ValidationError("found multiple Authorize.net transactions. total amount is greater than what we authorized. Please get in touch with the administrator.")
        return super(AccountMove, self.with_context({'create_payment': True})).payment_action_capture()

    def cron_capture_autherize_invoices(self):

        payment_terms = self.env['account.payment.term'].search([('is_pre_payment', '=', True)])

        invoices = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('invoice_payment_term_id', 'in', payment_terms.ids),
            ('authorized_transaction_ids', '!=', False),
            ('invoice_date_due', '<=', fields.Date.today())])


        transactions = invoices.mapped('authorized_transaction_ids').filtered(lambda r: r.state == 'authorized')

        for transaction in transactions:
            transaction.action_capture()
        failed_txs = transactions.filtered(lambda r: r.state == 'error')
        if failed_txs:
            failed_txs.mapped('invoice_ids').write({'is_authorize_tx_failed': True})
            failed_txs.mapped('invoice_ids').message_post(body='Failed to capture transaction.')
