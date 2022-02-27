# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class BatchPaymentCommon(models.Model):
    _inherit = ['mail.thread']
    _name = 'batch.payment.common'
    _description = "Batch Payment Common"

    name = fields.Char(string='Batch Name', default='New', copy=False, required=True, help='Name of the batch payment')
    cash_collected_lines = fields.One2many('cash.collected.lines', 'common_batch_id', string='Cash Collected Breakup')
    payment_ids = fields.One2many('account.payment', 'common_batch_id', string='Payments')
    actual_returned = fields.Float(string='Total Amount', required=1, digits='Product Price')
    is_posted = fields.Boolean(string="Posted")
    pending_amount = fields.Float(string="Difference", compute='_calculate_pending_amount')
    batch_payment_count = fields.Integer(string='Batch Payment', compute='_compute_batch_payment_count')
    cash_amount = fields.Float(string='Cash Amount', digits='Product Price')
    cheque_amount = fields.Float(string='Check Amount', digits='Product Price')
    show_warning = fields.Boolean(string='Pending Line Warning')
    state = state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Posted'),
        ('cancel', 'Cancelled')], default='draft', copy=False, tracking=True, required=True)
    card_amount = fields.Float(string='Credit card Amount', digits='Product Price')

    @api.depends('payment_ids')
    def _compute_batch_payment_count(self):
        for rec in self:
            rec.batch_payment_count = len(rec.payment_ids.mapped('batch_payment_id'))

    @api.depends('actual_returned', 'cash_collected_lines', 'cash_collected_lines.amount')
    def _calculate_pending_amount(self):
        for batch in self:
            real_collected = 0
            for cash_line in batch.cash_collected_lines:
                real_collected += float_round(cash_line.amount, precision_digits=2)
            batch.pending_amount = float_round(batch.actual_returned - real_collected, precision_digits=2)

    def register_payments(self):
        self.ensure_one()
        if not self.actual_returned:
            raise UserError('You cannot keep total amount field empty')
        if not self.cash_collected_lines:
            raise UserError('No lines to process')
        if self.cash_collected_lines and all(line.amount > 0 for line in self.cash_collected_lines):
            self.cash_collected_lines.create_payment()
        else:
            self.show_warning = True
            return self
        return self.write({
            'show_warning': False,
            'is_posted': True,
            'state': 'paid'
        })

    def view_batch_payments(self):
        self.ensure_one()
        payments = self.payment_ids
        batch_payments = payments.mapped('batch_payment_id')
        action = self.env.ref('account_batch_payment.action_batch_payment_in').read()[0]

        if len(batch_payments) > 1:
            action['domain'] = [('id', 'in', batch_payments.ids)]
        elif len(batch_payments) == 1:
            action['views'] = [(self.env.ref('account_batch_payment.view_batch_payment_form').id, 'form')]
            action['res_id'] = batch_payments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action

    def action_set_to_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})
