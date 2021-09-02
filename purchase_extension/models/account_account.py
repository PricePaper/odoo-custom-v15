# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    discount_due_date = fields.Date(compute='compute_discount_due_date', string='Discount Due Date', store=True)
    vendor_bill_receipt_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Autocomplete from Receipt'
    )
    bill_receipt_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Autocomplete From Receipt'
    )

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for invoice in self:
            if invoice.type == 'in_invoice':
                invoice.invoice_line_ids.mapped('purchase_line_id.order_id').button_done()
        return res

    @api.depends('payment_term_id.due_days', 'date_invoice')
    def compute_discount_due_date(self):
        for invoice in self:
            invoice.discount_due_date = False
            if invoice.date_invoice and invoice.payment_term_id and invoice.payment_term_id.due_days:
                invoice.discount_due_date = invoice.date_invoice + relativedelta(days=invoice.payment_term_id.due_days)

    def _prepare_invoice_line_from_stock_move_line(self, line):
        taxes = line.purchase_line_id.taxes_id
        invoice_line_tax_ids = line.purchase_line_id.order_id.fiscal_position_id.map_tax(taxes, line.product_id, line.purchase_line_id.order_id.partner_id)
        invoice_line = self.env['account.invoice.line']
        date = self.date or self.date_invoice
        price = line.price_unit
        if self.type == 'in_refund':
            price = -1 * price
        data = {
            'purchase_line_id': line.purchase_line_id.id,
            'name': line.picking_id.name + ': ' + line.product_id.name,
            'origin': line.picking_id.name,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': price,
            'quantity': line.quantity_done,
            'discount': 0.0,
            'account_analytic_id': line.purchase_line_id.account_analytic_id.id,
            'analytic_tag_ids': line.purchase_line_id.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        account = invoice_line.with_context(purchase_line_id=line.id).get_invoice_line_account('in_invoice', line.product_id, line.purchase_line_id.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data

    @api.onchange('bill_receipt_id')
    def bill_receipt_change(self):
        if not self.bill_receipt_id:
            return {}
        self.receipt_change_bill(self.bill_receipt_id)
        return{}

    @api.onchange('vendor_bill_receipt_id')
    def receipt_change(self):
        if not self.vendor_bill_receipt_id:
            return {}
        self.receipt_change_bill(self.bill_receipt_id)
        return{}

    def receipt_change_bill(self, receipt):
        if not self.partner_id:
            self.partner_id = receipt.partner_id.parent_id\
                and receipt.partner_id.parent_id.id\
                or receipt.partner_id.id

        if not self.invoice_line_ids:
            #as there's no invoice line yet, we keep the currency of the PO
            self.currency_id = receipt.mapped(
                'move_ids_without_package').mapped('purchase_line_id').mapped('order_id').currency_id

        new_lines = self.env['account.invoice.line']
        for line in receipt.mapped('move_ids_without_package'):
            data = self._prepare_invoice_line_from_stock_move_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.payment_term_id = self.partner_id.property_supplier_payment_term_id
        # receipt = False
        return {}


AccountInvoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
