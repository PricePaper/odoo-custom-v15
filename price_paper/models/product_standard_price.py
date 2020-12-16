# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class ProductStandardPrice(models.Model):
    _name = "product.standard.price"

    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    price = fields.Float(string="Standard Price")
    cost = fields.Float(string="cost")

ProductStandardPrice()
