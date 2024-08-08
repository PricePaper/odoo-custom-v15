# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    public_product_type = fields.Selection(selection=[
            ("delivery", "Delivery"),
            ("loyalty", "Loyalty")
        ], string='Public Product Type', default=False)

class ProductProduct(models.Model):
    _inherit = "product.product"

    delivery_carrier_ids = fields.One2many('delivery.carrier', 'product_id', string='Delivery Carrier')
