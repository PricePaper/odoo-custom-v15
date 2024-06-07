# -*- coding: utf-8 -*-


from odoo import api, models, fields


class Product(models.Model):
    _inherit = 'product.product'

    partner_product_names = fields.One2many('partner.product.name', 'product_id', string="Partner Defined Product Names")


class PartnerProductName(models.Model):
    _name = 'partner.product.name'
    _description = 'Partner custom product name'

    _sql_constraints = [('partner_id', 'unique(partner_id, product_id)', 'Each partner can only have one record.')]

    name = fields.Char('Product Name')
    partner_id = fields.Many2one('res.partner', string="Partner")
    product_id = fields.Many2one('product.product', string="Product")



