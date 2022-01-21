# -*- coding: utf-8 -*-

from odoo import fields, models


class FbprophetConfig(models.Model):
    _inherit = 'fbprophet.config'

    config_type = fields.Selection(selection_add=[('inventory', "Inventory Forecasting")])
    inv_config_for = fields.Selection(
        selection=[('global', 'Global'), ('categ', 'Product Category'), ('product', 'Product')],
        string='Inventory Config For')
    categ_id = fields.Many2one('product.category', string='Product Category')
    product_id = fields.Many2one('product.product', string='Product')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
