# -*- coding: utf-8 -*-
"""
    This model is used to create a product brand fields
"""
from odoo import api, fields, models


class ProductBrandEpt(models.Model):
    _name = 'product.brand.ept'
    _inherit = ['website.published.multi.mixin']
    _order = 'name'
    _description = 'Product Brand'

    name = fields.Char('Brand Name', required=True, translate=True)
    description = fields.Text('Description', translate=True)
    website_id = fields.Many2one("website", string="Website")
    logo = fields.Binary('Logo File')
    product_ids = fields.One2many('product.template', 'product_brand_ept_id', string="Products", readonly=True)
    products_count = fields.Integer(
        string='Number of products',
        compute='_compute_products_count',
        help='It shows the number of product counts',
    )
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of product Brands.", index=True,
                              default=10)
    is_brand_page = fields.Boolean('Is Brand Page', help="It will set the separate landing page for this brand")
    brand_page = fields.Many2one("website.page", string="Brand Page",
                                 help="Select the brand page which you want to set for this brand.")
    is_featured_brand = fields.Boolean('Is Featured Brand')

    @api.depends('product_ids')
    def _compute_products_count(self):
        """
        product count computation
        @return:
        """
        for product in self:
            product.products_count = len(product.product_ids)

    def set_brand_wizard(self):
        """
        action brand wizard
        @return: wizard-action
        """
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'product.brand.config',
            'name': "Product Brand Configuration",
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_brand_id': self.id},
        }
        return action
