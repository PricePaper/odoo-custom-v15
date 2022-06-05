from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PartialPayment(models.TransientModel):
    _name = "partial.payment.invoice"
    _description = "Partial Payment"

    payment_id = fields.Many2one('account.payment')
    partial_lines = fields.One2many('partial.payment.invoice.lines', 'partial_payment_id')

    def add_payment(self):
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
    invoice_id = fields.Many2one('account.move', 'Invoice')
    amount = fields.Float('Amount')
