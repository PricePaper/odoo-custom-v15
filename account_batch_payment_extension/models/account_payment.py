from odoo import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_delete_from_db(self):
        self.sudo().unlink()


AccountPayment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
