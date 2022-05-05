# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import UserError


class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def get_move_lines_for_bank_statement_line(self, st_line_id, partner_id=None, excluded_ids=None, search_str=False, offset=0, limit=None, mode=None):
        if mode == 'rp':
            aml_rec = self.env['account.move.line']
            batch_name = {}
            st_line = self.env['account.bank.statement.line'].browse(st_line_id)
            for batch in self.env['account.batch.payment'].search([('state', '!=', 'reconciled')], order='id asc'):
                if abs(batch.amount) == abs(st_line.amount):
                    lines = batch.payment_ids.mapped('move_id').mapped('line_ids').filtered(
                        lambda rec: rec.account_id.internal_type not in (
                            'receivable', 'payable') and rec.id not in excluded_ids or [])
                    batch_name.update({line: batch.name for line in lines})
                    aml_rec |= lines
            if not aml_rec:
                for common in self.env['batch.payment.common'].search([('actual_returned', '=', abs(st_line.amount))]):
                    lines = common.payment_ids.mapped('move_id').mapped('line_ids').filtered(
                        lambda rec: rec.account_id.internal_type not in (
                            'receivable', 'payable') and rec.id not in excluded_ids or [])
                    batch_name.update({line: common.name for line in lines})
                    aml_rec |= lines
            if aml_rec:
                js_vals_list = []
                recs_count = len(aml_rec)
                for line in aml_rec:
                    vals = self._prepare_js_reconciliation_widget_move_line(st_line, line, recs_count=recs_count)
                    vals.update({'name': '%s - %s' % (vals['name'], batch_name.get(line))})
                    js_vals_list.append(vals)
                if excluded_ids:
                    excluded_ids += aml_rec.ids
                else:
                    excluded_ids = aml_rec.ids
                js_vals = super(AccountReconciliation, self).get_move_lines_for_bank_statement_line(st_line_id, partner_id, excluded_ids, search_str, offset, limit, mode)
                for val in js_vals:
                    js_vals_list.append(val)
                return js_vals_list
        return super(AccountReconciliation, self).get_move_lines_for_bank_statement_line(st_line_id, partner_id, excluded_ids, search_str, offset, limit, mode)

    @api.model
    def process_bank_statement_line(self, st_line_ids, data):
        res = super().process_bank_statement_line(st_line_ids, data)
        # for statement in res['statement_line_ids']:
        #     reconciled_lines = statement.move_id.line_ids.mapped(
        #         'matched_debit_ids') + statement.move_id.line_ids.mapped('matched_credit_ids')
        #     reconciled_lines = (
        #             reconciled_lines.mapped('debit_move_id') + reconciled_lines.mapped('credit_move_id')).filtered(
        #         lambda rec: rec.id not in res['moves'].line_ids.ids)
        #     if len(reconciled_lines.mapped('journal_id')) == 1 and reconciled_lines.mapped(
        #             'journal_id').id != statement.journal_id.id and reconciled_lines.mapped(
        #         'journal_id').type == 'cash':
        #         for aml in reconciled_lines:
        #             if aml.journal_id.type == 'cash' and aml.debit > 0:
        #                 journal = self.env.ref('account_batch_payment_extension.account_journal_cash_to_bank')
        #                 if not journal:
        #                     raise UserError("Journal \"Cash to Bank\" is not configured")
        #                 move_vals = {
        #                     'date': statement.date,
        #                     'ref': 'Cash transfer to bank',
        #                     'company_id': statement.company_id.id,
        #                     'journal_id': journal.id,
        #                     'line_ids': [
        #                         [0, 0, {
        #                             'partner_id': statement.partner_id.id or False,
        #                             # 'move_id': move_id,
        #                             'debit': 0,
        #                             'credit': aml.debit,
        #                             'journal_id': journal.id,
        #                             'account_id': aml.account_id.id
        #                         }],
        #                         [0, 0, {
        #                             'partner_id': statement.partner_id.id or False,
        #                             # 'move_id': move_id,
        #                             'debit': aml.debit,
        #                             'credit': 0,
        #                             'journal_id': journal.id,
        #                             'account_id': journal.default_account_id.id
        #                         }]]
        #                 }
                        # self.env['account.move'].create(move_vals).action_post()
        for stmt in res['statement_line_ids']:
            if 'DEPOSITED ITEM RETURNED' in stmt.payment_ref:
                cheque_no = stmt.payment_ref and stmt.payment_ref.split('CK#:')
                if cheque_no and len(cheque_no) > 1:
                    cheque_no = cheque_no[1].split(' ', 1)[0]
                    cheque_no_strip = cheque_no.lstrip('0')
                    payment = self.env['account.payment'].search(['|',
                                                                  ('ref', '=', cheque_no_strip),
                                                                  ('ref', '=', cheque_no),
                                                                  ('amount', '=', abs(stmt.amount))])
                    vals = {'bank_stmt_line_id': stmt.id}
                    if payment and len(payment) == 1:
                        vals['payment_ids'] = [(6, 0, payment.ids)]
                        vals['partner_ids'] = [(6, 0, payment.mapped('partner_id').ids)]
                    if not payment and stmt.partner_id:
                        vals['partner_ids'] = [(6, 0, stmt.mapped('partner_id').ids)]
                    self.env['process.returned.check'].create(vals)
        return res


    @api.model
    def get_move_lines_by_batch_payment(self, st_line_id, batch_payment_id):
        st_line = self.env['account.bank.statement.line'].browse(st_line_id)
        move_lines = self.env['account.move.line']
        for payment in self.env['account.batch.payment'].browse(batch_payment_id).payment_ids:
            journal_accounts = [payment.journal_id.default_account_id.id, payment.journal_id.default_account_id.id]
            move_lines |= payment.line_ids.filtered(lambda r: r.account_id.id in journal_accounts)

        target_currency = st_line.currency_id or st_line.journal_id.currency_id or st_line.journal_id.company_id.currency_id
        if move_lines:
            return self._prepare_move_lines(move_lines, target_currency=target_currency, target_date=st_line.date)
        return super().get_move_lines_by_batch_payment(st_line_id, batch_payment_id)

AccountReconciliation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
