# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, date

from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date




class AccountRegisterPaymentLines(models.TransientModel):
    """
        New table to show payment lines and discount amount
    """
    _name = "account.register.payment.lines"
    _description = "Register Payment Lines"

    payment_id = fields.Many2one('account.payment', 'Payment')
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True)
    amount_total = fields.Monetary('Invoice Amount', related='invoice_id.amount_residual')
    currency_id = fields.Many2one('res.currency', 'Currency', related='invoice_id.currency_id')
    discounted_total = fields.Float('Actual Amount', compute="_get_discount_total")
    discount = fields.Float('Discount')
    discount_percentage = fields.Float('T.Disc(%)')
    reference = fields.Char(string="Reference")
    invoice_date = fields.Date('Invoice Date')
    payment_amount = fields.Float('Payment Amount')
    is_full_reconcile = fields.Boolean('Full')

    @api.depends('discount')
    def _get_discount_total(self):
        for line in self:
            discounted_total = 0.0
            if line.amount_total >= 0:
                discounted_total = line.amount_total - line.discount
            else:
                discounted_total = line.amount_total + line.discount
            line.discounted_total = discounted_total
 


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends("payment_lines")
    def _has_lines(self):
        for record in self:
            record.has_payment_lines = len(record.payment_lines) > 0 and True or False

    discount_amount = fields.Float('Discount Amount')
    payment_lines = fields.One2many('account.payment.lines', 'payment_id')
    has_payment_lines = fields.Boolean('Has Payment Lines?', compute="_has_lines")
    payment_reference = fields.Char('Payment Reference')
    discount_journal_id = fields.Many2one('account.move')
    discount_total = fields.Float('Total', compute="_get_discount")
    writeoff_account_id = fields.Many2one('account.account', 'Discount Account')


    @api.depends("payment_lines.discounted_total", "payment_lines.discount")
    def _get_discount(self):
        """ Update total amount and discount"""
        amount, discount_amount = 0, 0
        #TODO migrate this function
        self.discount_total = amount

class AccountPaymentLines(models.Model):
    _name = "account.payment.lines"
    _description = "Payment Lines"

    payment_id = fields.Many2one('account.payment', 'Payment')
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True)
    amount_total = fields.Monetary('Invoice Amount')
    currency_id = fields.Many2one('res.currency', 'Currency', related='invoice_id.currency_id')
    discounted_total = fields.Float('Actual Amount')
    discount = fields.Float('Discount')
    discount_percentage = fields.Float('T.Disc(%)')
    reference = fields.Char(string="Reference")
    invoice_date = fields.Datetime('Invoice Date')
    payment_amount = fields.Float('Payment Total')
    is_full_reconcile = fields.Boolean('Full')
    discount_journal_id = fields.Many2one('account.move', 'Discount Journal')



