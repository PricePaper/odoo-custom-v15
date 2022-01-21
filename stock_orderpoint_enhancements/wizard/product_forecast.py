# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductForecast(models.TransientModel):
    _name = 'product.forecast'
    _description = 'Show product Forecast'
    _order = 'date desc'

    date = fields.Date(string='Date')
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Product Quantity")
    quantity_max = fields.Float(string="Product Quantity Max")
    quantity_min = fields.Float(string="Product Quantity Min")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
