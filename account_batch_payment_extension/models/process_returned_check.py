# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round


class ProcessReturnedCheck(models.Model):
    _inherit = ['mail.thread']
    _name = 'process.returned.check'
    _description = 'Process Returned Check'

    bank_stmt_line_id = fields.Many2one('account.bank.statement.line', string='Bank statement line')
    payment_ids = fields.Many2many('account.payment', string='Payment')
    partner_ids = fields.Many2many('res.partner', string='Partner')
    invoice_ids = fields.Many2many('account.move', string='Invoice')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], default='draft', copy=False, tracking=True, required=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoice_count', readonly=True)
    notes = fields.Text(string='Notes')
    amount = fields.Monetary(related='bank_stmt_line_id.amount', string='Amount',currency_field='journal_currency_id')
    journal_currency_id = fields.Many2one('res.currency', string="Journal's Currency", related='bank_stmt_line_id.currency_id', readonly=True,
                                          help='Utility field to express amount currency')

    @api.depends('invoice_ids')
    def _get_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.mapped('invoice_ids'))

    def process_payment(self):
        for rec in self:
            if not rec.payment_ids:
                raise UserError("Payment is not selected")

            payment = rec.payment_ids

            if float_round(abs(rec.amount), 2) != float_round(sum(payment.mapped('amount')), 2):
                raise UserError("Amount mismatch.")
            invoice = payment.mapped('reconciled_invoice_ids')

            for pay in payment:
                pay.write({'old_invoice_ids': [(6, 0, pay.reconciled_invoice_ids.ids)]})
                pay.move_id.mapped('line_ids').filtered(lambda r: r.account_id.internal_type in ('payable', 'receivable')).remove_move_reconcile()

            if not self.bank_stmt_line_id.partner_id:
                partner = False
                if self.partner_ids:
                    partner = self.partner_ids
                else:
                    partner = payment.mapped('partner_id')
                if partner:
                    self.bank_stmt_line_id.line_ids.write({'partner_id': partner[0].id})
            reconcile_lines = (payment.mapped('line_ids') | self.bank_stmt_line_id.line_ids)
            reconcile_lines = reconcile_lines.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
            reconcile_lines.reconcile()

            if invoice:
                fine_invoices = invoice.remove_sale_commission(self.bank_stmt_line_id.date)
                if fine_invoices:
                    self.invoice_ids = fine_invoices
            rec.state = 'done'
            payment.write({'is_return_cleared': True})
            rec.bank_stmt_line_id.is_return_cleared = True

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.sudo().env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


ProcessReturnedCheck()
