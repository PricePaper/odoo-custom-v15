# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    is_discount = fields.Boolean('Is Cash Discount', help="Check this box if this payment term is \
        a cash discount. If cash discount is used the remaining amount of the invoice will not be paid")
    discount_days = fields.Integer('Discount Days', required=False,
                                   help="Discount will be applicable if paid within these days")
    discount = fields.Float('Discount (%)', digits=(4, 2))

    @api.onchange('is_discount')
    def onchange_is_discount(self):
       if self.is_discount is False:
           self.discount_days = False
           self.discount = False


AccountPaymentTerm()
