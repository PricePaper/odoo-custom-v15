# -*- coding: utf-8 -*-

from odoo import api, models, fields


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    payment_method = fields.Selection([('ach-debit', 'ACH-Debit')], string="Payment Method")
