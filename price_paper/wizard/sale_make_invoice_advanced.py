# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection([
        ('delivered', 'Invoiceable lines'),
        ('all', 'Invoiceable lines (deduct down payments)'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')
    ], string='What do you want to invoice?', default='all', required=True)


SaleAdvancePaymentInv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
