# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_driver_writeoff_account = fields.Boolean(string='Driver Writeoff Account',
                                                help='Check this box if this is the driver writeoff account.')


AccountAccount()


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def button_cancel(self):
        for move in self:
            if not move.journal_id.update_posted or not self.env.user.has_group('account.group_account_manager'):
                raise UserError(
                    _('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
        return super(AccountMove, self).button_cancel()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
