from odoo import models, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_delete_from_db(self):
        self.batch_payment_id.message_post(body='Payment line removed.')
        self.sudo().unlink()

    def action_remove_from_batch(self):
        self.write({'batch_payment_id': False})

    @api.model
    def create(self, vals):
        record = super(AccountPayment, self).create(vals)
        if record.batch_payment_id:
            record.batch_payment_id.message_post(body='Payment line created.')
        return record


AccountPayment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
