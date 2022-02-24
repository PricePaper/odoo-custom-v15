# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.payment.register"

    def _post_payments(self, to_process, edit_mode=False):
        """
        override to post discount move if exist
        """
        res = super()._post_payments(to_process, edit_mode)
        if edit_mode:
            for vals in to_process:
                payment = vals['payment']
                if payment.discount_move_id:
                    payment.discount_move_id.action_post()
        return res

    def _reconcile_payments(self, to_process, edit_mode=False):
        """
        reconcile the discount move
        """
        res = super()._reconcile_payments(to_process, edit_mode)
        if edit_mode:
            vals = to_process[0]
            payment = vals.get('payment')
            if payment.partner_type == 'customer' and payment.discount_move_id:
                discount_limit = self.env['ir.config_parameter'].sudo().get_param('accounting_extension.customer_discount_limit', 5.00)
                if isinstance(discount_limit, str):
                    discount_limit = float(discount_limit)
                discount_limit = sum(payment.reconciled_invoice_ids.mapped('amount_total')) * (discount_limit / 100)
                if payment.discount_move_id.amount_total > discount_limit:
                    raise UserError('Invoices can not be discounted more than $ %.2f.\nCreate a credit memo instead.' % discount_limit)
            counterpart_line = vals.get('to_reconcile')
            counterpart_line |= payment.discount_move_id.line_ids.filtered(lambda r: r.account_id.user_type_id.type in ('receivable', 'payable'))
            counterpart_line.reconcile()
        return res

    def _init_payments(self, to_process, edit_mode=False):
        """
        create discount move from write of vals
        seperating it from payment journal
        to keep the uniqueness
        """
        write_off_vals = False
        if edit_mode:
            for vals in to_process:
                write_off_vals = vals['create_vals'].pop('write_off_line_vals', False)
        payments = super()._init_payments(to_process, edit_mode)
        if write_off_vals:
            destination_account_id = payments.partner_id and payments.partner_id.property_account_receivable_id or self.env['ir.property']._get(
                'property_account_receivable_id', 'res.partner')
            if payments.partner_type == 'supplier':
                destination_account_id = payments.partner_id and payments.partner_id.property_account_payable_id or self.env['ir.property']._get(
                    'property_account_payable_id', 'res.partner')
            discount_move = self.env['account.move'].create({
                'move_type': 'entry',
                'company_id': payments.company_id.id,
                'date': fields.Date.today(),
                'journal_id': payments.journal_id.id,
                'ref': '%s - Discount' % payments.ref,
                'line_ids': [(0, 0, {
                    'account_id': destination_account_id.id,
                    'company_currency_id': payments.company_id.currency_id.id,
                    'credit': 0.0 if payments.partner_type == 'supplier' else write_off_vals.get('amount', 0),
                    'debit': write_off_vals.get('amount', 0) if payments.partner_type == 'supplier' else 0.0,
                    'journal_id': payments.journal_id.id,
                    'name': write_off_vals.get('name'),
                    'partner_id': payments.partner_id.id
                }), (0, 0, {
                    'account_id': write_off_vals.get('account_id'),
                    'company_currency_id': payments.company_id.currency_id.id,
                    'credit': write_off_vals.get('amount', 0) if payments.partner_type == 'supplier' else 0.0,
                    'debit': 0.0 if payments.partner_type == 'supplier' else write_off_vals.get('amount', 0),
                    'journal_id': payments.journal_id.id,
                    'name': write_off_vals.get('name'),
                    'partner_id': payments.partner_id.id
                })]
            })
            payments.write({'discount_move_id': discount_move.id})
        return payments


AccountRegisterPayment()


class AccountPayment(models.Model):
    _inherit = "account.payment"

    discount_move_id = fields.Many2one('account.move', 'Discount Move')


AccountPayment()
