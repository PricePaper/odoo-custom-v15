# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # field used in search view
    discount_date = fields.Date('Discount Till')

    def button_draft(self):
        executed_ids = self.env['account.move']
        for move in self.filtered(lambda r: r.move_type != 'entry'):
            discount_line = move.get_discount_line()
            if discount_line:
                discount_move = discount_line.mapped('move_id')
                if discount_move:
                    discount_move.button_draft()
                    discount_move.button_cancel()
        if not self.env.user.has_group('base.group_system'):
            res = super(AccountMove, self).button_draft()
            self.write({'discount_date': False})
            return res
        for move in self:
            if self.statement_line_id:
                st_line = move.statement_line_id
                move.statement_line_id = False
                super(AccountMove, move).button_draft()
                move.statement_line_id = st_line.id
                executed_ids |= move
        res = super(AccountMove, self-executed_ids).button_draft()
        self.write({'discount_date': False})
        return res


    def js_remove_outstanding_partial(self, partial_id):
        # remove discount if payment is cancelled
        discount_move_id = self.env['account.move']
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        payment = self.env['account.payment'].search([('move_id', 'in', [partial.debit_move_id.move_id.id, partial.credit_move_id.move_id.id])])
        if payment and payment.discount_move_id:
            discount_move_id = payment.discount_move_id
        if not discount_move_id:
            moves = partial.debit_move_id.move_id + partial.credit_move_id.move_id
            discount_accounts = self.env.user.company_id.discount_account_id + self.env.user.company_id.purchase_writeoff_account_id
            for move in moves:
                if len(move.line_ids) == 2 and all(line.name == 'Discount' for line in move.line_ids) and any(line.account_id.id in discount_accounts.ids for line in move.line_ids):
                    discount_move_id = move
                    break
        res = super().js_remove_outstanding_partial(partial_id)

        if discount_move_id:
            discount_move_id.line_ids.remove_move_reconcile()
            discount_move_id.button_cancel()
            discount_move_id.unlink()
        return res

    def action_show_discount_popup(self):
        # add discount
        return {
            'name': 'Customer Discount',
            'view_mode': 'form',
            'res_model': 'add.discount',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'type': self.move_type}
        }

    # todo not used. We can use the default unreconcile feature for discount
    # todo golive remove before
    # def _get_reconciled_vals(self, partial, amount, counterpart_line):
    #     res = super()._get_reconciled_vals(partial, amount, counterpart_line)
    #     if not counterpart_line.payment_id and counterpart_line.name == 'Discount':
    #         res.update({'is_discount': True})
    #     return res

    def compute_taxes(self):
        self.ensure_one()
        self._recompute_tax_lines(recompute_tax_base_amount=True)

    def get_discount_line(self):
        """
        return discount move lines
        """
        self.ensure_one()
        reconciled_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        reconciled_amls = reconciled_lines.mapped('matched_debit_ids.debit_move_id') + \
                          reconciled_lines.mapped('matched_credit_ids.credit_move_id')
        moves = reconciled_amls.move_id
        if self.move_type == 'out_invoice':
            discount_account = self.company_id.discount_account_id
            discount_line = moves.mapped('line_ids').filtered(lambda rec: rec.account_id.id == discount_account.id)
            return discount_line
        elif self.move_type == 'in_invoice':
            discount_account = self.company_id.purchase_writeoff_account_id
            discount_line = moves.mapped('line_ids').filtered(lambda rec: rec.account_id.id == discount_account.id)
            return discount_line
        return self.env['account.move.line']

    def get_discount(self):
        """
        return total discount amount
        """
        self.ensure_one()
        discount_line = self.get_discount_line()
        if discount_line:
            if self.move_type == 'out_invoice':
                return sum(discount_line.mapped('debit'))
            elif self.move_type == 'in_invoice':
                return sum(discount_line.mapped('credit'))
        return 0

    def action_post(self):
        """
        override to set discount days
        """
        res = super(AccountMove, self).action_post()
        if self.invoice_payment_term_id and self.invoice_payment_term_id.is_discount:
            self.discount_date = self.invoice_date + relativedelta(days=self.invoice_payment_term_id.due_days)
        return res

    # def button_draftaa(self):
    #     res = super(AccountMove, self).button_draft()
    #     self.write({'discount_date': False})
    #     return res

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super()._get_last_sequence_domain(relaxed)
        if self.move_type == 'out_refund':
            where_string += " AND sequence_prefix ilike 'RINV/%%' "
        return where_string, param



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def reconcile(self):
        ''' Reconcile the current move lines all together.
        :return: A dictionary representing a summary of what has been done during the reconciliation:
                * partials:             A recorset of all account.partial.reconcile created during the reconciliation.
                * full_reconcile:       An account.full.reconcile record created when there is nothing left to reconcile
                                        in the involved lines.
                * tax_cash_basis_moves: An account.move recordset representing the tax cash basis journal entries.
        '''

        results = {}

        if not self:
            return super(AccountMoveLine, self).reconcile()
        for line in self:
            if line.reconciled:
                raise UserError(_("You are trying to reconcile some entries that are already reconciled."))
            if not line.account_id.reconcile and line.account_id.internal_type != 'liquidity':
                raise UserError(_("Account %s does not allow reconciliation. First change the configuration of this account to allow it.")
                                % line.account_id.display_name)
            if line.move_id.state != 'posted':
                raise UserError(_('You can only reconcile posted entries. %s' % line.move_id.name))
        return super(AccountMoveLine, self).reconcile()



"""
this class is used to remove discount from payemnt if payment un reconciled now this is achived in js_remove_outstanding_partial method
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def get_related_discount_lines(self, invoice_id=False):
        discount_lines = self.env['account.move.line']
        for account_move_line in self:
            payment = account_move_line.payment_id
            if payment and payment.discount_journal_id:
                discount_journal = payment.discount_journal_id
                discount_lines |= discount_journal.line_ids.filtered(
                    lambda r: r.account_id.user_type_id.type in ('receivable', 'payable'))
            elif invoice_id and payment:
                payment_line = payment.payment_lines.filtered(lambda r: r.invoice_id.id == invoice_id)
                discount_lines |= payment_line.discount_journal_id.line_ids.filtered(
                    lambda r: r.account_id.user_type_id.type in ('receivable', 'payable'))
        return discount_lines

    def remove_move_reconcile(self):
        invoice_id = self._context.get('invoice_id')
        discount_lines = self.get_related_discount_lines(invoice_id)
        res = super(AccountMoveLine, (self | discount_lines)).remove_move_reconcile()
        discount_lines.mapped('move_id').button_cancel()
        discount_lines.mapped('move_id').unlink()
        return res

    def remove_active_discount(self, invoice_id=False):
        for account_move_line in self:
            discount_lines = account_move_line.get_related_discount_lines(invoice_id) | account_move_line
            discount_lines.remove_move_reconcile()
            discount_lines.mapped('move_id').button_cancel()
            discount_lines.mapped('move_id').unlink()
        return True
"""
