# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(
        selection_add=[('all', 'Invoiceable lines (deduct down payments)')],
        string='What do you want to invoice?',
        default='all',
        required=True,
        ondelete={'all': lambda recs: recs.write({'advance_payment_method': 'delivered'})}
    )


SaleAdvancePaymentInv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
