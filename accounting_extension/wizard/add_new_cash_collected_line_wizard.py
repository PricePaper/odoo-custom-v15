# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class CashCollectedLinesWizard(models.TransientModel):
    _name = 'cash.collected.lines.wizard'
    _description = 'Cash Collected Line Wizard'

    batch_id = fields.Many2one('stock.picking.batch', string='Batch')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    amount = fields.Float(string='Amount Collected', digits='Product Price')
    communication = fields.Char(string='Memo')
    payment_method_id = fields.Many2one('account.payment.method', domain=[('payment_type', '=', 'inbound')])
    is_communication = fields.Boolean(string='Is Communication')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['bank', 'cash'])])
    invoice_id = fields.Many2one('account.move')
    discount = fields.Float(string='Discount(%)')
    search_wizard_id = fields.Many2one('add.cash.collected.wizard', string='Parent')
    available_payment_method_ids = fields.One2many('account.payment', compute='_compute_available_payment_method_ids')
    discount_amount = fields.Float(string='Discount', digits='Product Price')


    @api.depends('journal_id')
    def _compute_available_payment_method_ids(self):
        for record in self:
            pass


class CashCollectedWizard(models.TransientModel):
    _name = 'add.cash.collected.wizard'
    _description = "Add Cash Collected Line With partner Not In The Batch Line"


    cash_collected_line_ids = fields.One2many('cash.collected.lines.wizard', 'search_wizard_id', string="Cash Collected Lines")


    def add_cash_collected_lines(self):
        """
        Creating cash collected line
        """
        self.ensure_one()
 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
