# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class CashCollectedLinesWizard(models.TransientModel):
    _name = 'cash.collected.lines.wizard'
    _description = 'Cash Collected Line Wizard'

    batch_id = fields.Many2one('stock.picking.batch', string='Batch')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    amount = fields.Float(string='Amount Collected', digits=dp.get_precision('Product Price'))
    communication = fields.Char(string='Memo')
    payment_method_id = fields.Many2one('account.payment.method', domain=[('payment_type', '=', 'inbound')])
    is_communication = fields.Boolean(string='Is Communication')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['bank', 'cash'])])
    invoice_id = fields.Many2one('account.invoice')
    discount = fields.Float(string='Discount(%)')
    search_wizard_id = fields.Many2one('add.cash.collected.wizard', string='Parent')
    available_payment_method_ids = fields.One2many(comodel_name='account.payment', compute='_compute_available_payment_method_ids')
    discount_amount = fields.Float(string='Discount', digits=dp.get_precision('Product Price'))

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id:
            self.amount = self.invoice_id.residual
            days = (self.invoice_id.date_invoice - fields.Date.context_today(self)).days
            if self.invoice_id.payment_term_id.is_discount and abs(days) < self.invoice_id.payment_term_id.due_days:
                self.discount = self.invoice_id.payment_term_id.discount_per
                self.discount_amount = self.invoice_id.residual * (self.discount / 100)
                self.amount = self.invoice_id.residual - self.discount_amount
            else:
                self.discount = 0

    @api.onchange('discount')
    def onchange_discount(self):
        if self.invoice_id:
            self.discount_amount = self.invoice_id.residual * (self.discount / 100)
            print('PPPPP', self.discount_amount)
            self.amount = self.invoice_id.residual - self.discount_amount

    @api.onchange('discount_amount')
    def onchange_discount_amount(self):
        if self.invoice_id:
            self.discount = (self.discount_amount / self.invoice_id.residual) * 100
            self.amount = self.invoice_id.residual - self.discount_amount

    @api.onchange('payment_method_id')
    def _onchange_payment_method_id(self):
        self.is_communication = self.payment_method_id.code == 'check_printing'

    @api.depends('journal_id')
    def _compute_available_payment_method_ids(self):
        for record in self:
            record.available_payment_method_ids = record.journal_id.inbound_payment_method_ids.ids

CashCollectedLinesWizard()


class CashCollectedWizard(models.TransientModel):
    _name = 'add.cash.collected.wizard'
    _description = "Add Cash Collected Line With partner Not In The Batch Line"


    cash_collected_line_ids = fields.One2many('cash.collected.lines.wizard', 'search_wizard_id', string="Cash Collected Lines")

    @api.multi
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
                'payment_method_id': line_id.payment_method_id.id,
                'sequence': sequence
                    }

        self.env['cash.collected.lines'].create(cash_lines)
        return True


CashCollectedWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
