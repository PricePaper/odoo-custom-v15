# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    discount_due_date = fields.Date(compute='compute_discount_due_date', string='Discount Due Date', store=True)
    vendor_bill_receipt_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Autocomplete from Receipt'
    )
    bill_receipt_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Autocomplete From Receipt'
    )

    @api.depends('invoice_payment_term_id.due_days', 'invoice_date')
    def compute_discount_due_date(self):
        for invoice in self:
            if invoice.invoice_date and invoice.invoice_payment_term_id and invoice.invoice_payment_term_id.due_days:
                invoice.discount_due_date = invoice.invoice_date + relativedelta(days=invoice.invoice_payment_term_id.due_days)
            else:
                invoice.discount_due_date = False

    def _prepare_invoice_line_from_stock_move_line(self, line):

        po_line = line.purchase_line_id
        price = line.price_unit
        if self.move_type == 'in_refund':
            price = -1 * price
        data = {
            'display_type': po_line.display_type,
            'sequence': po_line.sequence,
            'name': '%s: %s' % (po_line.order_id.name, po_line.name),
            'product_id': po_line.product_id.id,
            'product_uom_id': po_line.product_uom.id,
            'quantity': line.quantity_done,
            'price_unit': price,
            'tax_ids': [(6, 0, po_line.taxes_id.ids)],
            'analytic_account_id': po_line.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, po_line.analytic_tag_ids.ids)],
            'purchase_line_id': po_line.id,
            'move_id': self.id,
        }
        accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=line.purchase_line_id.order_id.fiscal_position_id)
        account = accounts['expense']

        if account:
            data['account_id'] = account.id
        return data

    @api.onchange('bill_receipt_id')
    def bill_receipt_change(self):
        if not self.bill_receipt_id:
            return {}
        self.receipt_change_bill(self.bill_receipt_id)
        self.bill_receipt_id = False
        return {}

    @api.onchange('vendor_bill_receipt_id')
    def receipt_change(self):
        if not self.vendor_bill_receipt_id:
            return {}
        self.receipt_change_bill(self.vendor_bill_receipt_id)
        self.vendor_bill_receipt_id = False
        return {}

    def receipt_change_bill(self, receipt):
        if not self.partner_id:
            self.partner_id = receipt.partner_id.parent_id \
                              and receipt.partner_id.parent_id.id \
                              or receipt.partner_id.id
        purchase = receipt.mapped('move_lines').mapped('purchase_line_id').mapped('order_id')

        if not purchase:
            raise ValidationError(_('Receipt Does not have any PO.'))

        invoice_vals = purchase.with_company(purchase.company_id)._prepare_invoice()
        invoice_vals['currency_id'] = self.line_ids and self.currency_id or invoice_vals.get('currency_id')
        del invoice_vals['ref']
        self.update(invoice_vals)

        new_lines = self.env['account.move.line']
        for line in receipt.mapped('move_lines'):
            data = self._prepare_invoice_line_from_stock_move_line(line)
            new_line = new_lines.new(data)
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            new_lines += new_line
        # self.invoice_line_ids += new_lines
        new_lines._onchange_mark_recompute_taxes()

        # Compute invoice_origin.
        origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))

        # Compute ref.
        refs = self._get_invoice_reference()
        self.ref = ', '.join(refs)

        # Compute payment_reference.
        if len(refs) == 1:
            self.payment_reference = refs[0]

        self._onchange_currency()
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
