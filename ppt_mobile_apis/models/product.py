# -*- coding: utf-8 -*-

from odoo import api, models, fields

class Product(models.Model):
    _inherit = 'product.product'

    portal_qty_available = fields.Float(
        'Portal qty On Hand', compute='_compute_portal_quantity',
        digits='Product Unit of Measure')


    def _compute_portal_quantity(self):
        
        for product in self:
            product.portal_qty_available = product.sudo().quantity_available
