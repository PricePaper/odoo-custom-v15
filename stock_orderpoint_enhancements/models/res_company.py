# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    delay = fields.Integer(string='Delivery Lead Time',
                           default=21,
                           help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse.")
    buffer_percentages = fields.Text(string='OrderPoint Buffer percentages',
                                     help="One configuration per line. Format is 'comparison':'percent as decimal'. "
                                          "Example: <=5:0.20")
    order_freq = fields.Integer(string='Order Frequency', default=30)


ResCompany()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
