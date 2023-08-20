# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # field used in search view
    discount_date = fields.Date('Discount Till')

    @api.onchange('invoice_date', 'highest_name', 'company_id')
    def _onchange_invoice_date(self):
        super(AccountMove, self)._onchange_invoice_date()
        if self.invoice_date and self.move_type in ['in_invoice', 'in_refund']:
            user_lock_date = self.company_id._get_user_fiscal_lock_date()
            if self.invoice_date > user_lock_date:
                self.date = self.invoice_date

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
        # update preferred payment method
        self._compute_preferred_payment_method_idd()
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

    def wrapper_cancel_csb(self):
        for move in self:
            move.button_draft()
            move.button_cancel()
        return self.ids

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft)
        # update preferred payment method
        self._compute_preferred_payment_method_idd()
        return res

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



    def _prepare_reconciliation_partials(self):
        """
            Override to split the payment
            calling from partial payment wizard
        """

        if not self._context.get('is_partial_payment', False):
            return super(AccountMoveLine, self)._prepare_reconciliation_partials()
        # amount = self._context.get('partial_amount')
        def fix_remaining_cent(currency, abs_residual, partial_amount):
            if abs_residual - currency.rounding <= partial_amount <= abs_residual + currency.rounding:
                return abs_residual
            else:
                return partial_amount

        debit_lines = iter(self.filtered(lambda line: line.balance > 0.0 or line.amount_currency > 0.0))
        credit_lines = iter(self.filtered(lambda line: line.balance < 0.0 or line.amount_currency < 0.0))
        debit_line = None
        credit_line = None

        debit_amount_residual = 0.0
        debit_amount_residual_currency = 0.0
        credit_amount_residual = 0.0
        credit_amount_residual_currency = 0.0
        debit_line_currency = None
        credit_line_currency = None

        partials_vals_list = []

        while True:

            # Move to the next available debit line.
            if not debit_line:
                debit_line = next(debit_lines, None)
                if not debit_line:
                    break
                debit_amount_residual = self._context.get('partial_amount')#debit_line.amount_residual

                if debit_line.currency_id:
                    debit_amount_residual_currency = self._context.get('partial_amount')#debit_line.amount_residual_currency
                    debit_line_currency = debit_line.currency_id
                else:
                    debit_amount_residual_currency = debit_amount_residual
                    debit_line_currency = debit_line.company_currency_id

            # Move to the next available credit line.
            if not credit_line:
                credit_line = next(credit_lines, None)
                if not credit_line:
                    break
                credit_amount_residual = credit_line.amount_residual

                if credit_line.currency_id:
                    credit_amount_residual_currency = credit_line.amount_residual_currency
                    credit_line_currency = credit_line.currency_id
                else:
                    credit_amount_residual_currency = credit_amount_residual
                    credit_line_currency = credit_line.company_currency_id

            min_amount_residual = min(debit_amount_residual, -credit_amount_residual)
            has_debit_residual_left = not debit_line.company_currency_id.is_zero(debit_amount_residual) and debit_amount_residual > 0.0
            has_credit_residual_left = not credit_line.company_currency_id.is_zero(credit_amount_residual) and credit_amount_residual < 0.0
            has_debit_residual_curr_left = not debit_line_currency.is_zero(debit_amount_residual_currency) and debit_amount_residual_currency > 0.0
            has_credit_residual_curr_left = not credit_line_currency.is_zero(credit_amount_residual_currency) and credit_amount_residual_currency < 0.0
            if debit_line_currency == credit_line_currency:
                # Reconcile on the same currency.

                # The debit line is now fully reconciled because:
                # - either amount_residual & amount_residual_currency are at 0.
                # - either the credit_line is not an exchange difference one.
                if not has_debit_residual_curr_left and (has_credit_residual_curr_left or not has_debit_residual_left):
                    debit_line = None
                    continue

                # The credit line is now fully reconciled because:
                # - either amount_residual & amount_residual_currency are at 0.
                # - either the debit is not an exchange difference one.
                if not has_credit_residual_curr_left and (has_debit_residual_curr_left or not has_credit_residual_left):
                    credit_line = None
                    continue

                min_amount_residual_currency = min(debit_amount_residual_currency, -credit_amount_residual_currency)
                min_debit_amount_residual_currency = min_amount_residual_currency
                min_credit_amount_residual_currency = min_amount_residual_currency

            else:
                # Reconcile on the company's currency.

                # The debit line is now fully reconciled since amount_residual is 0.
                if not has_debit_residual_left:
                    debit_line = None
                    continue

                # The credit line is now fully reconciled since amount_residual is 0.
                if not has_credit_residual_left:
                    credit_line = None
                    continue

                min_debit_amount_residual_currency = credit_line.company_currency_id._convert(
                    min_amount_residual,
                    debit_line.currency_id,
                    credit_line.company_id,
                    credit_line.date,
                )
                min_debit_amount_residual_currency = fix_remaining_cent(
                    debit_line.currency_id,
                    debit_amount_residual_currency,
                    min_debit_amount_residual_currency,
                )
                min_credit_amount_residual_currency = debit_line.company_currency_id._convert(
                    min_amount_residual,
                    credit_line.currency_id,
                    debit_line.company_id,
                    debit_line.date,
                )
                min_credit_amount_residual_currency = fix_remaining_cent(
                    credit_line.currency_id,
                    -credit_amount_residual_currency,
                    min_credit_amount_residual_currency,
                )

            debit_amount_residual -= min_amount_residual
            debit_amount_residual_currency -= min_debit_amount_residual_currency
            credit_amount_residual += min_amount_residual
            credit_amount_residual_currency += min_credit_amount_residual_currency

            partials_vals_list.append({
                'amount': min_amount_residual,
                'debit_amount_currency': min_debit_amount_residual_currency,
                'credit_amount_currency': min_credit_amount_residual_currency,
                'debit_move_id': debit_line.id,
                'credit_move_id': credit_line.id,
            })
        return partials_vals_list


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
