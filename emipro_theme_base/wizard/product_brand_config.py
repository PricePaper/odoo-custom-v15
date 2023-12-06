"""
@author: Emipro Technologies Pvt. Ltd.
"""
from odoo import models, fields, api


class ProductBrandConfig(models.TransientModel):
    """
    Class to handel brand configuration wizard
    """
    _name = 'product.brand.config'
    _description = "Product Brand Configuration Wizard"

    brand_id = fields.Many2one('product.brand.ept', string="Brand")
    product_ids = fields.Many2many('product.template')

    @api.onchange('brand_id')
    def onchange_brand_id(self):
        """
        onechange of brand ID
        @return: -
        """
        #set the brand into wizard
        self.write({
            'product_ids': [(6, 0, self.brand_id.product_ids.ids)]
        })

    def config_brand_product(self):
        """
        unset if any and set to the select : configure brand to product
        @return: Boolean
        """
        #unset if any and set to the select
        if self.brand_id:
            self.brand_id.product_ids.write({'product_brand_ept_id': False})
            self.product_ids.write({'product_brand_ept_id': self.brand_id})
        return True
