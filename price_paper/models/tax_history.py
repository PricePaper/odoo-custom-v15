# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleTaxHistory(models.Model):
    _name = 'sale.tax.history'
    _description = 'Sales Tax History'

    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Product')
    tax = fields.Boolean(string='Tax applicable')


SaleTaxHistory()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
