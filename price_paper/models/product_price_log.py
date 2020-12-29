# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductPriceLog(models.Model):
    _name = 'product.price.log'
    _description = 'Product Price Log'

    product_id = fields.Many2one('product.product', string='Product')
    change_date = fields.Datetime(string='Date')
    old_price = fields.Float(string='Old Price')
    new_price = fields.Float(string='New Price')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    type = fields.Selection(string='Type',
                            selection=[('cost', 'Cost'),
                                       ('burden', 'Burden Percentage'),
                                       ('std_price', 'Standard Price'),
                                       ('pricelist_price', 'Pricelist Price')])
    user_id = fields.Many2one('res.users', string='User')


ProductPriceLog()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
