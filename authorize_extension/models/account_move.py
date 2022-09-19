# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'


    def payment_action_capture(self):
        return super(AccountMove, self.with_context({'create_payment': True})).payment_action_capture()
