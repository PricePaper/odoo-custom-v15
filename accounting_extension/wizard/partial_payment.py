from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_compare


class PartialPayment(models.TransientModel):
    _name = "partial.payment.invoice"
    _description = "Partial Payment"

    payment_id = fields.Many2one('account.payment')
    partial_lines = fields.One2many('partial.payment.invoice.lines', 'partial_payment_id')
    balance_to_pay = fields.Float(related="payment_id.balance_to_pay", string="Pending Amount")
    amount_total = fields.Float('Total', compute="_compute_amount_total")

    @api.depends('partial_lines.amount', 'partial_lines')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(self.partial_lines.mapped('amount'))

    def add_payment(self):
        if (-1 * self.balance_to_pay) < self.amount_total:
            raise ValidationError("You cannot pay more than what we have")
        domain = [
            ('parent_state', '=', 'posted'),
            ('account_internal_type', 'in', ('receivable', 'payable')),
            ('reconciled', '=', False),
        ]
        payment_lines = self.payment_id.line_ids.filtered_domain(domain)
        for inv in self.partial_lines:
            inv_lines = inv.invoice_id.line_ids.filtered_domain(domain)
            (payment_lines+inv_lines).with_context({'is_partial_payment': True, 'partial_amount': inv.amount}).reconcile()
        return  True


class PartialPaymentLines(models.TransientModel):
    _name = "partial.payment.invoice.lines"
    _description = "Partial Payment Lines"

    partial_payment_id = fields.Many2one('partial.payment.invoice')
    payment_id = fields.Many2one('account.payment', related="partial_payment_id.payment_id")
    partner_id = fields.Many2one('res.partner', related="payment_id.partner_id")
    invoice_id = fields.Many2one('account.move', 'Invoice', required=True)
    currency_id = fields.Many2one('res.currency', related="invoice_id.currency_id")
    amount_residual = fields.Monetary(string='Amount Due', related="invoice_id.amount_residual", currency_field='currency_id')
    amount = fields.Float('Amount')

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount > self.amount_residual:
            self.amount = 0
            return {
            'warning': {
                'title': "Warning",
                'message': "You cannot pay more than amount due",
                'type': 'notification'
            },



            }
