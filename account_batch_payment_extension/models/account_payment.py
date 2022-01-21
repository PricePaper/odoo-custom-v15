# -*- coding: utf-8 -*-

from odoo import models, api, fields

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_return_cleared = fields.Boolean(string='Return cleared')
    old_invoice_ids = fields.Many2many('account.move', string='Old Invoices')

    def action_delete_from_db(self):
        self.batch_payment_id.message_post(body='Payment line removed.')
        self.sudo().unlink()

    def action_remove_from_batch(self):
        self.write({'batch_payment_id': False, 'state':'posted'})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
