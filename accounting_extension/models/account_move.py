# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_date = fields.Date('Discount Till')

    def action_show_discount_popup(self):
        return {
            'name': 'Customer Discount',
            'view_mode': 'form',
            'res_model': 'add.discount',
            # 'res_id': self.id,
            # 'view_id': self.env.ref('batch_delivery.view_writeoff_discount_window_view_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'type': self.move_type}
        }

    def _get_reconciled_vals(self, partial, amount, counterpart_line):
        res = super()._get_reconciled_vals(partial, amount, counterpart_line)
        if not counterpart_line.payment_id and counterpart_line.name == 'Discount':
            res.update({'is_discount': True})
        return res

    def compute_taxes(self):
        self.ensure_one()
        self._recompute_tax_lines(recompute_tax_base_amount=True)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    def get_related_discount_lines(self, invoice_id=False):
        discount_lines = self.env['account.move.line']
        for account_move_line in self:
            payment = account_move_line.payment_id
            if payment and payment.discount_journal_id:
                discount_journal = payment.discount_journal_id
                discount_lines |= discount_journal.line_ids.filtered(lambda r: r.account_id.user_type_id.type in ('receivable', 'payable'))
            elif invoice_id and payment:
                payment_line = payment.payment_lines.filtered(lambda r: r.invoice_id.id == invoice_id)
                discount_lines |= payment_line.discount_journal_id.line_ids.filtered(lambda r: r.account_id.user_type_id.type in ('receivable', 'payable'))
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
