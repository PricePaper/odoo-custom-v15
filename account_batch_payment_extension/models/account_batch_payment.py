# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    is_posted = fields.Boolean(compute='_compute_is_posted')
    state = fields.Selection(selection_add=[('cancel', 'Cancelled')])
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method', readonly=False, store=True, copy=False, required=True,
                                             tracking=True, domain="[('id', 'in', available_payment_method_line_ids)]")
    payment_method_id = fields.Many2one(related='payment_method_line_id.payment_method_id', string="Method", store=True)
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line', compute='_compute_payment_method_line_fields')

    @api.onchange('payment_method_line_id')
    def onchange_payment_method(self):
        if self.payment_method_line_id and self.payment_ids.filtered(
                lambda rec: rec.payment_method_line_id != self.payment_method_line_id) or not self.payment_method_id and self.payment_ids:
            raise ValidationError(
                "you cannot change the payment method. Since some other lines are using this payment method\nIf you want to change the payment method you have to remove all the lines")

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        self.payment_method_line_id = False

    @api.depends('journal_id', 'batch_type')
    def _compute_payment_method_line_fields(self):
        for record in self:
            record.available_payment_method_line_ids = record.journal_id._get_available_payment_method_lines(record.batch_type)

    @api.depends('payment_ids.state')
    def _compute_is_posted(self):
        for record in self:
            record.is_posted = False
            if record.payment_ids and record.payment_ids.filtered(lambda r: r.state == 'posted'):
                record.is_posted = True

    def validate_batch_button(self):
        self.ensure_one()
        if not self.is_posted:
            raise ValidationError('Please post all payment lines before validate.')
        if self.payment_ids.filtered(lambda rec: rec.journal_id != self.journal_id or rec.payment_method_line_id != self.payment_method_line_id):
            payment_name = self.payment_ids.filtered(
                lambda rec: rec.journal_id != self.journal_id or rec.payment_method_line_id != self.payment_method_line_id).mapped('name')
            raise ValidationError("some payments are not belongs to same journal/payment method\n%s" % payment_name)
        return super(AccountBatchPayment, self).validate_batch_button()


    def add_payment(self):
        return {
            'name': 'Create Payment',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_id': self.env.ref('account_batch_payment_extension.batch_payment_add_payment_wizard').id,
            'context': {
                'default_payment_type': self.batch_type,
                'default_partner_type': 'customer',
                'default_journal_id': self.journal_id.id,
                'default_batch_payment_id': self.id,
                'default_payment_method_line_id': self.payment_method_line_id.id
            }
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
