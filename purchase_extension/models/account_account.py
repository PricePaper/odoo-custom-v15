# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


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
            invoice.discount_due_date = False
            # if invoice.invoice_date and invoice.invoice_payment_term_id and invoice.invoice_payment_term_id.due_days:
            #     invoice.discount_due_date = invoice.invoice_date + relativedelta(days=invoice.payment_term_id.due_days)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
