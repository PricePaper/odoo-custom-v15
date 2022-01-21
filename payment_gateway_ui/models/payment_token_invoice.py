# -*- coding: utf-8 -*-

from odoo import models, fields, api
import hashlib
from datetime import datetime


class PaymentTokenInvoice(models.Model):
    _name = 'payment.token.invoice'
    _description="Payment Token Invoice"

    token = fields.Char("Payment token", size=128, help="Unique identifier for retrieving an EDI document.")
    invoice_id = fields.Many2one('account.move')
    order_id = fields.Many2one('sale.order', string="Order")
    state = fields.Selection(
        [('draft', 'Not Visited Yet'), ('visited', 'Visited'), ('submitted', 'Submitted'), ('paid', 'Payed'),
         ('expired', 'Expired'), ('error', 'Error')], string='Visitor Status', default='draft', readonly=True)
    model = fields.Selection(
        [('sale', 'Sale'), ('invoice', 'Invoice')], string='Model', readonly=True)


