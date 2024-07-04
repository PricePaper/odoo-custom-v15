# -*- coding: utf-8 -*-

from odoo import api, models, fields

class Product(models.Model):
    _inherit = 'product.product'


    def get_product_qty_available(self):

        product_qty = []
        for product in self:
            product = product.sudo()
            product_qty.append({'product_id': product.id, 'quantity': product.quantity_available})
        return product_qty
