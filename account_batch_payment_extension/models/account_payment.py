# -*- coding: utf-8 -*-

from odoo import models, api, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_return_cleared = fields.Boolean(string='Return cleared')
    old_invoice_ids = fields.Many2many('account.move', string='Old Invoices')

    @api.depends('state')
    def _compute_batch_payment_id(self):
        for payment in self:
            payment.batch_payment_id = payment.batch_payment_id or None

    def action_delete_from_db(self):
        self.batch_payment_id.message_post(body='Payment %s removed.' % self.name)
        self.sudo().unlink()

    def action_remove_from_batch(self):
        self.write({'batch_payment_id': False})

    def action_cancel(self):
        """
        Mark batch payment to cancel if all it's payment are in cancel state
        """
        batch_payment_ids = self.mapped('batch_payment_id')
        mark_to_cancel = self.env['account.batch.payment']
        res = super(AccountPayment, self).action_cancel()
        for batch_payment in batch_payment_ids:
            payment_states = batch_payment.payment_ids.mapped('state')
            if all(state == 'cancel' for state in payment_states):
                mark_to_cancel |= batch_payment
        mark_to_cancel.write({'state': 'cancel'})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
