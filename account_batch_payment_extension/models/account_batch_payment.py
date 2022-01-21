# -*- coding: utf-8 -*-

from odoo import models,fields, api
from odoo.exceptions import UserError


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    is_posted = fields.Boolean(compute='_compute_is_posted')

    @api.depends('payment_ids.state')
    def _compute_is_posted(self):
        for record in self:
            record.is_posted = False if record.payment_ids.filtered(lambda r: r.state == 'draft') else True if record.payment_ids else False

    def validate_batch(self):
        if not self.is_posted:
            raise UserError('Please post all payment lines before validate.')
        return super(AccountBatchPayment, self).validate_batch()

    def post_payments(self):
        self.with_context(prevent_post=False).normalize_payments()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
