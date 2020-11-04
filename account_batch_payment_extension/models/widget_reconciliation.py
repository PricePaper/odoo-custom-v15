# -*- coding: utf-8 -*-

from odoo import models, api


class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def get_move_lines_for_bank_statement_line(self, st_line_id, partner_id=None, excluded_ids=None, search_str=False,
                                               offset=0, limit=None):
        batch = self.get_batch_payments_data(None)
        if batch and not self._context.get('action', False):
            result = []
            move_lines = self.env['account.move.line']
            batchObj = self.env['account.batch.payment']
            st_line = self.env['account.bank.statement.line'].browse(st_line_id)
            for batch_rec in batch:
                payments = batchObj.browse(batch_rec['id']).payment_ids
                if partner_id:
                    payments = payments.filtered(lambda rec: rec.partner_id.id == partner_id)
                for payment in payments:
                    journal_accounts = [payment.journal_id.default_debit_account_id.id,
                                        payment.journal_id.default_credit_account_id.id]
                    move_lines |= payment.move_line_ids.filtered(lambda r: r.account_id.id in journal_accounts)

                target_currency = st_line.currency_id or st_line.journal_id.currency_id or st_line.journal_id.company_id.currency_id

                result.extend(
                    self._prepare_move_lines(move_lines, target_currency=target_currency, target_date=st_line.date))
            return result
        return super(AccountReconciliation, self).get_move_lines_for_bank_statement_line(st_line_id, partner_id,
                                                                                         excluded_ids, search_str,
                                                                                         offset, limit)
