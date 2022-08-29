# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    is_pre_payment = fields.Boolean('Is prepayment?', help="The payment will be authorised while confirming a sale order if this is enabled.")


AccountPaymentTerm()
