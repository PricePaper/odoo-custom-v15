# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductPriceLog(models.Model):
    _name = 'product.price.log'
    _description = 'Product Price Log'

    product_id = fields.Many2one('product.product', string='Product')
    change_date = fields.Datetime(string='Date')
    old_price = fields.Float(string='Old Price', digits='Product Price')
    new_price = fields.Float(string='New Price', digits='Product Price')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    partner_ids = fields.Many2many('res.partner', string='Partner')
    price_from = fields.Selection(string='From',
                            selection=[('sale', 'Sale Order'),
                                       ('manual', 'Manual'),
                                       ('standard', 'Standard Price Cron'),
                                       ('cost_cron', 'Cost Change Cron'),
                                       ('global_price', 'Global Price Change'),
                                       ('purchase', 'Purchase Order')])
    uom_id = fields.Many2one('uom.uom', string='UOM')
    type = fields.Selection(string='Type',
                            selection=[('cost', 'Cost'),
                                       ('burden', 'Burden Percentage'),
                                       ('std_price', 'Standard Price'),
                                       ('pricelist_price', 'Pricelist Price'),
                                       ('vendor_price', 'Vendor Price')])
    user_id = fields.Many2one('res.users', string='User')
    min_qty = fields.Float(string='Min Qty')
    trace_log = fields.Text(string='Log')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
