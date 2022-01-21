# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round
from odoo.exceptions import UserError

#todo not migrated we can do after finishing other modules
class BatchPaymentCommon(models.Model):
    _inherit = ['mail.thread']
    _name = 'batch.payment.common'
    _description = "Batch Payment Common"

    name = fields.Char(string='Batch Picking Name', default='New',
                       copy=False, required=True, help='Name of the batch payment')
    cash_collected_lines = fields.One2many('cash.collected.lines', 'common_batch_id',
                                           string='Cash Collected Breakup')
    payment_ids = fields.One2many('account.payment', 'common_batch_id', string='Payments')
    actual_returned = fields.Float(string='Total Amount',
                                   help='Total amount returned by the driver.',
                                   digits='Product Price')
    is_posted = fields.Boolean(string="Posted")
    pending_amount = fields.Float(string="Difference",
                                  compute='_calculate_pending_amount')
    batch_payment_count = fields.Integer(string='Batch Payment',
                                         compute='_compute_batch_payment_count')
    cash_amount = fields.Float(string='Cash Amount',
                               digits='Product Price')
    cheque_amount = fields.Float(string='Check Amount',
                                 digits='Product Price')
    show_warning = fields.Boolean(string='Pending Line Warning')
    state = state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')], default='draft',
        copy=False, tracking=True, required=True)
    card_amount = fields.Float(string='Credit card Amount',
                               digits='Product Price')

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
        for batch in self:
            if not batch.actual_returned:
                raise UserError(_('Please properly enter the returned amount'))
            if not batch.cash_collected_lines:
                raise UserError(_('Please add cash collected lines before proceeding.'))
            if batch.cash_collected_lines and all(l.amount > 0 for l in batch.cash_collected_lines):
                batch.cash_collected_lines.create_from_common_batch_payment()
            else:
                batch.show_warning = True
                return
            batch.show_warning = False
            batch.is_posted = True
            batch.state = 'paid'

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
