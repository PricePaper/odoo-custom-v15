# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    check_bounce_product = fields.Many2one('product.product', string='Check Bounce Product')


ResCompany()
