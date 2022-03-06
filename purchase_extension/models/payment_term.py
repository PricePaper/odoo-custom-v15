# -*- coding: utf-8 -*-

from odoo import models, fields


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    order_type = fields.Selection([('purchase', 'Purchase'), ('sale', 'Sale')], string='Type')
    code = fields.Char(string='Code')
    due_days = fields.Integer(string='Discount Days')
    discount_per = fields.Float(string='Discount Percent')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
