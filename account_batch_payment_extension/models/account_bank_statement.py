# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    is_return_cleared = fields.Boolean('Return cleared')

    # def button_undo_reconciliation(self):
    #     result = super(AccountBankStatementLine, self).button_undo_reconciliation()
    #     for st_line in self:
    #         st_line.partner_id = False
    #     return result

    def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the liquidity account.
        - The lines using the transfer account.
        - The lines being not in one of the two previous categories.
        :return: (liquidity_lines, suspense_lines, other_lines)
        '''
        liquidity_lines, suspense_lines, other_lines = super()._seek_for_lines()

        if not liquidity_lines:
            journal_id = self.journal_id
            if self.journal_id.code == 'BNK1':
                journal_id = self.journal_id.search([('code', '=', 'CSH1')], limit=1)
            for line in self.move_id.line_ids:
                if line.account_id == journal_id.default_account_id:
                    liquidity_lines |= line
                elif line.account_id == journal_id.suspense_account_id:
                    suspense_lines |= line
                else:
                    other_lines |= line
        return liquidity_lines, suspense_lines, other_lines


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
