# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        counterpart_moves = super().process_reconciliation(counterpart_aml_dicts=counterpart_aml_dicts, payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
        statement_line = counterpart_moves.mapped('line_ids').mapped('statement_line_id')
        for stmt in statement_line:
            if stmt.name == 'DEPOSIT_RETURN':
                cheque_no = stmt.ref and stmt.ref.split('CK#:')
                if cheque_no and len(cheque_no) > 1:
                    cheque_no = cheque_no[1].split(' ', 1)[0]
                    cheque_no_strip = cheque_no.lstrip('0')
                    payment = self.env['account.payment'].search(['|', ('communication', '=', cheque_no_strip), ('communication', '=', cheque_no)])
                    if payment:
                        invoice = payment.invoice_ids
                        payment.move_line_ids.remove_move_reconcile()
                        reconcile_lines = (payment.move_line_ids | counterpart_moves.line_ids)
                        reconcile_lines = reconcile_lines.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                        reconcile_lines.reconcile()
                        invoice.remove_sale_commission()
        return counterpart_moves

AccountBankStatementLine()



class AccountReconcileModel(models.Model):
    _inherit = 'account.reconcile.model'

    @api.multi
    def _apply_rules(self, st_lines, excluded_ids=None, partner_map=None):
        res = super()._apply_rules(st_lines, excluded_ids, partner_map)
        batch_payemnt = {'inbound': self.env['account.batch.payment'], 'outbound': self.env['account.batch.payment']}

        for p in self.env['account.batch.payment'].search([('state', '!=', 'reconciled')]):
            if p.batch_type == 'inbound':
                batch_payemnt['inbound'] |= p
            else:
                batch_payemnt['outbound'] |= p

        for line in st_lines:
            line_residual = line.currency_id and line.amount_currency or line.amount
            if line_residual > 0:
                batch = batch_payemnt['inbound'].filtered(lambda rec: rec.amount == abs(line_residual))
                if batch:
                    for aml in batch.mapped('payment_ids').mapped('move_line_ids'):
                        if aml.debit:
                            res.get(line.id, {}).get('aml_ids', []).append(aml.id)
            else:
                batch = batch_payemnt['outbound'].filtered(lambda rec: rec.amount == abs(line_residual))
                if batch:
                    for aml in batch.mapped('payment_ids').mapped('move_line_ids'):
                        if aml.credit:
                            res.get(line.id, {}).get('aml_ids', []).append(aml.id)

        return res



AccountReconcileModel()
