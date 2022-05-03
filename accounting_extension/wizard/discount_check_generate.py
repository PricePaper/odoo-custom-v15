# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GenerateDiscountCheck(models.TransientModel):
    _name = 'generate.discount.check'
    _description = 'Generate Discount Check'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    wizard_invoice_ids = fields.One2many('vendor.bill.lines.wizard', 'generate_check_id', string='Invoices')

    @api.onchange('start_date', 'end_date')
    def get_invoices(self):
        if self.start_date and self.end_date:
            vendor_bills = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'),
                                                            ('payment_state', 'not in', ('in_payment', 'paid')),
                                                            ('discount_due_date', '>', self.start_date),
                                                            ('discount_due_date', '<', self.end_date)])
            vendor_bills |= self.env['account.move'].search(
                [('move_type', '=', 'in_invoice'), ('payment_state', 'not in', ('in_payment', 'paid')),
                 ('state', '=', 'posted'), ('invoice_date', '>', self.start_date), ('invoice_date', '<', self.end_date),
                 ('discount_due_date', '=', False)])

            self.wizard_invoice_ids = False
            lines = []
            for bill in vendor_bills:
                if bill.amount_residual <= 0:
                    continue
                if bill.discount_due_date and bill.discount_due_date >= fields.Date.today():
                    discount = bill.amount_residual * (100 - bill.invoice_payment_term_id.discount_per) / 100
                else:
                    discount = bill.amount_residual
                lines.append((0, 0, {
                    'total_amount': bill.amount_residual,
                    'partner_id': bill.partner_id.id,
                    'discount_amount': bill.amount_residual - discount,
                    'invoice_id': bill.id,
                    'date_invoice': bill.invoice_date,
                    'date_due': bill.invoice_date_due,
                    'discount_due_date': bill.discount_due_date,
                    'discounted_total': discount,
                }))
            self.wizard_invoice_ids = lines

    def generate_check(self):
        bank_journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        if not bank_journal:
            raise UserError('Bank journal not defined! \nPlease create a bank journal in the system to process these transactions.')
        # payment_method = self.env['account.payment.method'].search([('code', '=', 'check_printing'), ('payment_type', '=', 'outbound')], limit=1)
        payment_method_line = bank_journal.outbound_payment_method_line_ids.filtered(lambda rec: rec.code == 'check_printing' and rec.payment_type == 'outbound')
        if not payment_method_line:
            raise UserError('payment method Check is not defined! \nPlease create a payment method in bank journal to process these transactions.')
        if len(payment_method_line) > 1:
            payment_method_line = payment_method_line[0]
        # self.env['account.payment.method.line'].search([('payment_method_id', '=', payment_method.id),
        #                                                                   ('journal_id', '=', bank_journal.id)], limit=1)
        purchase_writeoff_account = self.env.user.company_id.purchase_writeoff_account_id
        if not purchase_writeoff_account:
            raise UserError('Please add a purchase writeoff account in the company form page.')

        for invoice in self.wizard_invoice_ids.filtered(lambda rec: rec.select):
            bill = invoice.invoice_id
            if bill.discount_due_date and bill.discount_due_date >= fields.Date.today():
                discount_move = self.env['add.discount'].with_context(active_id=bill.id).create({
                    'discount_type': 'amount',
                    'discount': invoice.discount_amount
                }).create_discount()
        return self.env['account.payment.register'].with_context({
            'active_model': 'account.move',
            'default_journal_id': bank_journal.id,
            'default_payment_method_line_id': payment_method_line.id,
            'active_ids': self.wizard_invoice_ids.filtered(lambda rec: rec.select).mapped('invoice_id').ids
        }).create({'group_payment': True}).action_create_payments()


GenerateDiscountCheck()


class VendorBillLines(models.TransientModel):
    _name = 'vendor.bill.lines.wizard'
    _description = 'Vendor Bill Lines Wizard'

    total_amount = fields.Float(string='Total')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    discount_amount = fields.Float('Discount')
    discounted_total = fields.Float('Due')
    invoice_id = fields.Many2one('account.move', string='Invoice Source')
    generate_check_id = fields.Many2one('generate.discount.check', string='Parent')
    date_invoice = fields.Date(string='Bill Date')
    date_due = fields.Date(string='Due Date')
    discount_due_date = fields.Date(string='Discount Date')
    select = fields.Boolean(string='Select', default=True)


VendorBillLines()
