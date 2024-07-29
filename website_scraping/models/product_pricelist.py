# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    competitor_id = fields.Many2one('website.scraping.cofig', string='Competitor')
    competietor_margin = fields.Float(string='Competitor Margin%',
                                      help='Margin From Competitor Price. When pricelist is auto updated, this margin is considered.')

class CustomerProductPrice(models.Model):
    _inherit = 'customer.product.price'

    price_last_fetched = fields.Date(string='Price last Fetched', readonly=True)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
