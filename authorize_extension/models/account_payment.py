from odoo import models, fields, api
from odoo.tools.float_utils import float_round


class AccountPayment(models.Model):
    _inherit = "account.payment"

    card_payment_type = fields.Selection(selection=[('bank', "Direct Bank"), ('authorize', "Through Authorize"), ], string="Card Swipe Payment Type")
    transaction_fee = fields.Monetary(
        string="Transaction Fee",
        compute='_compute_transaction_fee'
    )

    @api.depends('transaction_ids')
    def _compute_transaction_fee(self):
        """
        Sum all the transaction fee amount for which state
        is in 'authorized' or 'done'
        """
        for payment in self:
            payment.transaction_fee = 0
            if payment.payment_transaction_id.filtered(
                lambda tx: tx.state in ('authorized', 'done')):
                payment.transaction_fee = sum(
                    payment.payment_transaction_id.filtered(
                        lambda tx: tx.state in ('authorized', 'done')
                    ).mapped('transaction_fee')
                )

    def _prepare_payment_transaction_vals(self, **extra_create_values):
        res = super(AccountPayment, self)._prepare_payment_transaction_vals(**extra_create_values)
        count = self.env['payment.transaction'].search_count([('reference', 'ilike', res['reference'])])
        if count > 0:
            res['reference'] = "%s-%s" % (res['reference'], count)
        payment_fee = float(self.env['ir.config_parameter'].sudo().get_param('authorize_extension.card_fee') or 0.00)
        if payment_fee:
            res['amount'] = float_round(self.amount, precision_digits=2)
            res['transaction_fee'] = float_round((self.amount_total * (100 / (100+payment_fee))) * (payment_fee / 100), precision_digits=2)
        return res

    def action_cancel(self):
        res = super().action_cancel()
        for payment in self:
            if payment.payment_transaction_id and payment.payment_transaction_id.transaction_fee_move_id:
                payment.payment_transaction_id.transaction_fee_move_id.button_cancel()
        return res

    def action_post(self):
        res = super().action_post()
        for payment in self:
            if payment.payment_transaction_id and payment.payment_transaction_id.state == 'done' and payment.payment_transaction_id.transaction_fee and payment.payment_transaction_id.transaction_fee_move_id:
                # payment.payment_transaction_id.transaction_fee_move_id.post()
                (self.payment_id.line_ids + payment.payment_transaction_id.transaction_fee_move_id.line_ids).filtered(
                    lambda line: line.account_id == self.payment_id.destination_account_id and not line.reconciled
                ).reconcile()
        return res

    def _create_payment_transaction(self, **extra_create_values):
        transaction = super()._create_payment_transaction(**extra_create_values)
        if transaction.transaction_fee:
            transaction.create_transaction_fee_move(False)
        return transaction


AccountPayment()


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    transaction_fee = fields.Float('Transaction fee', compute="_compute_transaction_fee")

    @api.depends("amount", "payment_token_id")
    def _compute_transaction_fee(self):
        for payment in self:
            payment.transaction_fee = 0.0
            if payment.payment_token_id:
                transaction_fee = float(self.env['ir.config_parameter'].sudo().get_param('authorize_extension.card_fee') or 0.00)
                payment.transaction_fee = payment.source_amount * (transaction_fee / 100)

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date', 'transaction_fee',
                 'payment_token_id')
    def _compute_amount(self):
        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.amount = wizard.source_amount_currency + wizard.transaction_fee
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.amount = wizard.source_amount + wizard.transaction_fee
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id,
                                                                                 wizard.payment_date or fields.Date.today())
                wizard.amount = amount_payment_currency + wizard.transaction_fee

    @api.depends('amount', 'transaction_fee')
    def _compute_payment_difference(self):
        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.payment_difference = (wizard.source_amount_currency + wizard.transaction_fee) - wizard.amount
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.payment_difference = (wizard.source_amount + wizard.transaction_fee) - wizard.amount
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id,
                                                                                 wizard.payment_date or fields.Date.today())
                wizard.payment_difference = (amount_payment_currency + wizard.transaction_fee) - wizard.amount

    def _reconcile_payments(self, to_process, edit_mode=False):
        res = super(AccountPaymentRegister, self)._reconcile_payments(to_process, edit_mode)
        for vals in to_process:
            payment = vals['payment']
            if payment.payment_transaction_id and payment.reconciled_invoice_ids:
                if payment.reconciled_invoice_ids not in payment.payment_transaction_id.invoice_ids:
                    payment.payment_transaction_id.write({
                        'invoice_ids': [(4, inv.id) for inv in payment.reconciled_invoice_ids if
                                        inv not in payment.payment_transaction_id.invoice_ids],
                        'sale_order_ids': [(4, sale.id) for sale in
                                           payment.reconciled_invoice_ids.mapped('invoice_line_ids').mapped('sale_line_ids.order_id') if
                                           sale not in payment.payment_transaction_id.sale_order_ids]
                    })
        return res


AccountPaymentRegister()
