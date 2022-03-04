# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AddDiscount(models.TransientModel):
    _name = "add.discount"
    _description = "Add discount to invoice"

    discount = fields.Float(string='Discount($)')
    discount_type = fields.Selection([('percentage', 'Discount(%)'), ('amount', 'Discount($)')], default='percentage')

    def create_discount(self):
        self.ensure_one()
        move = self.env['account.move'].browse(self._context.get('active_id', 0))
        account_receivable = move.partner_id and move.partner_id.property_account_receivable_id
        account_payable = move.partner_id and move.partner_id.property_account_payable_id
        if not account_receivable:
            account_receivable = self.env['ir.property']._get('property_account_receivable_id', 'res.partner')
        if not account_payable:
            account_payable = self.env['ir.property']._get('property_account_payable_id', 'res.partner')

        if move.move_type == 'in_invoice':
            discount_account = move.company_id.purchase_writeoff_account_id
        else:
            discount_account = move.company_id.discount_account_id
        company_currency = move.company_id.currency_id

        if not discount_account:
            raise UserError('Please choose a discount account in company.')
        discount_limit = self.env['ir.config_parameter'].sudo().get_param('accounting_extension.customer_discount_limit', 5.00)
        if isinstance(discount_limit, str):
            discount_limit = float(discount_limit)

        discount_limit = move.amount_total * (discount_limit / 100)
        discount_amount = self.discount
        if self.discount_type == 'percentage':
            discount_amount = move.amount_total * (self.discount / 100)
        if move.move_type == 'out_invoice' and discount_amount > discount_limit:
            raise UserError('Invoices can not be discounted more than $ %.2f. \nCreate a credit memo instead.' % discount_limit)

        if float_compare(discount_amount, move.amount_residual, precision_digits=2) > 0:
            raise UserError('Cannot add discount more than residual $ %.2f' % move.amount_residual)

        discount_move = self.env['account.move'].create({
            'move_type': 'entry',
            'company_id': move.company_id.id,
            'date': fields.Date.today(),
            'journal_id': move.journal_id.id,
            'ref': '%s - Discount' % move.name,
            'line_ids': [(0, 0, {
                'account_id': account_payable.id if self.env.context.get('type') == 'in_invoice' else account_receivable.id,
                'company_currency_id': company_currency.id,
                'credit': 0.0 if move.move_type == 'in_invoice' else discount_amount,
                'debit': discount_amount if move.move_type == 'in_invoice' else 0.0,
                'journal_id': move.journal_id.id,
                'name': 'Discount',
                'partner_id': move.partner_id.id
            }), (0, 0, {
                'account_id': discount_account.id,
                'company_currency_id': company_currency.id,
                'credit': discount_amount if move.move_type == 'in_invoice' else 0.0,
                'debit': 0.0 if move.move_type == 'in_invoice' else discount_amount,
                'journal_id': move.journal_id.id,
                'name': 'Discount',
                'partner_id': move.partner_id.id
            })]
        })
        if not self._context.get('force_stop'):
            discount_move.action_post()
            aml = move.line_ids.filtered(
                lambda r: r.account_id.user_type_id.type in ('receivable', 'payable'))
            aml |= discount_move.line_ids.filtered(lambda r: r.account_id.user_type_id.type in ('receivable', 'payable'))
            aml.reconcile()

        return discount_move

    @api.model
    def create_truck_discount(self, batch_discount=0):
        if batch_discount:
            return self.create({'discount': batch_discount, 'discount_type': 'amount'}).create_discount()
        return False
