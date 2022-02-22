# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class CashCollectedLinesWizard(models.TransientModel):
    _name = 'cash.collected.lines.wizard'
    _description = 'Cash Collected Line Wizard'

    batch_id = fields.Many2one('stock.picking.batch', string='Batch')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    amount = fields.Float(string='Amount Collected', digits='Product Price')
    communication = fields.Char(string='Memo')
    payment_method_line_id = fields.Many2one('account.payment.method.line', domain=[('payment_type', '=', 'inbound')])
    is_communication = fields.Boolean(string='Is Communication')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['bank', 'cash'])])
    invoice_id = fields.Many2one('account.move')
    discount = fields.Float(string='Discount(%)')
    search_wizard_id = fields.Many2one('add.cash.collected.wizard', string='Parent')
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line', compute='_compute_available_payment_method_ids')
    discount_amount = fields.Float(string='Discount', digits='Product Price')


    @api.depends('journal_id')
    def _compute_available_payment_method_ids(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines('inbound')

    def check_discount_validity(self, amount, discount_per=False, discount_amount=False):
        customer_discount_per = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_extension.customer_discount_limit', 5.00)
        if isinstance(customer_discount_per, str):
            customer_discount_per = float(customer_discount_per)
        discount_amount_limit = round(amount * (customer_discount_per / 100), 2)
        if customer_discount_per and (customer_discount_per < discount_per or discount_amount_limit < discount_amount):
            raise UserError('Cannot add discount more than {}%.'.format(customer_discount_per))
        return True

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id:
            self.amount = self.invoice_id.amount_total
            days = (self.invoice_id.invoice_date - fields.Date.context_today(self)).days
            if self.invoice_id.invoice_payment_term_id.is_discount and abs(
                    days) < self.invoice_id.invoice_payment_term_id.due_days:
                discount_per = self.invoice_id.invoice_payment_term_id.discount_per
                discount_amount = self.invoice_id.amount_residual_signed * (self.discount / 100)
                self.check_discount_validity(self.invoice_id.amount_residual_signed, discount_per=discount_per,
                                             discount_amount=discount_amount)
                self.discount = self.invoice_id.invoice_payment_term_id.discount_per
                self.discount_amount = discount_amount
                self.amount = self.invoice_id.amount_residual_signed - discount_amount
            else:
                self.discount = 0
        else:
            self.discount = 0
            self.discount_amount = 0
            self.amount = 0


    @api.onchange('discount')
    def onchange_discount(self):
        self = self.with_context(recursive_onchanges=False)
        if self.invoice_id:
            self.check_discount_validity(self.invoice_id.amount_residual_signed, discount_per=self.discount)
            self.discount_amount = round(self.invoice_id.amount_residual_signed * (self.discount / 100), 2)
            self.amount = self.invoice_id.amount_residual_signed - self.discount_amount
        else:
            self.discount = 0
            self.discount_amount = 0
            return {'warning': {'message': 'for giving discount you must have a choose an invoice'}}

    @api.onchange('discount_amount')
    def onchange_discount_amount(self):
        self = self.with_context(recursive_onchanges=False)
        if self.invoice_id:
            self.check_discount_validity(self.invoice_id.amount_residual_signed, discount_amount=self.discount_amount)
            self.discount = round((self.discount_amount / self.invoice_id.amount_residual_signed) * 100, 2)
            self.amount = self.invoice_id.amount_residual_signed - self.discount_amount
        else:
            self.discount = 0
            self.discount_amount = 0
            return {'warning': {'message': 'for giving discount you must have a choose an invoice'}}


    @api.onchange('payment_method_id')
    def _onchange_payment_method_id(self):
        self.is_communication = self.payment_method_id.code == 'check_printing'

class CashCollectedWizard(models.TransientModel):
    _name = 'add.cash.collected.wizard'
    _description = "Add Cash Collected Line With partner Not In The Batch Line"


    cash_collected_line_ids = fields.One2many('cash.collected.lines.wizard', 'search_wizard_id', string="Cash Collected Lines")


    def add_cash_collected_lines(self):
        """
        Creating cash collected line
        """
        self.ensure_one()
        active_id = self._context.get('active_id')
        batch_id = self.env['stock.picking.batch'].browse(active_id)
        sequence = batch_id.cash_collected_lines.mapped('sequence')
        if sequence:
            sequence = max(sequence) + 1
        line_ids = self.cash_collected_line_ids
        for line_id in line_ids:
            cash_lines = {
                'partner_id': line_id.partner_id.id,
                'amount': line_id.amount,
                'communication': line_id.communication,
                'batch_id': batch_id.id,
                'invoice_id': line_id.invoice_id.id,
                'journal_id': line_id.journal_id.id,
                'discount': line_id.discount,
                'payment_method_line_id': line_id.payment_method_line_id.id,
                'sequence': sequence
                    }

            self.env['cash.collected.lines'].create(cash_lines)
        return True
 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
