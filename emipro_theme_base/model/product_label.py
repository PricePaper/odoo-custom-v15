# -*- coding: utf-8 -*-
"""
    This model is used to create a product line field
"""
from odoo import models, fields, api
from odoo.osv import expression


class ProductLabel(models.Model):
    _name = "product.label"
    _description = "Product Label"

    name = fields.Char("Name", required=True, translate=True, help="Name of the sale label")
    font_html_color = fields.Char('Font Color', help="Here you can set a specific HTML color index "
                                                     "(e.g. #ff0000) to display the color of product label text.")
    html_color = fields.Char(
        string='Color',
        help="Here you can set a specific HTML color index (e.g. #ff0000) to display the color of product label.")
    label_style = fields.Selection([
        ('style_1', 'Style 1'), ('style_2', 'Style 2'), ('style_3', 'Style 3'),
        ('style_4', 'Style 4'), ('style_5', 'Style 5')], string="Select the style for label",
                                   required=True, default='style_1', readonly=False)


class ProductLabelLine(models.Model):
    """
    class to handel peoduct tab lines
    """
    _name = "product.label.line"
    _description = 'Product Template Label Line'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template Id', required=True)
    website_id = fields.Many2one('website', string="Website", required=True)
    label = fields.Many2one('product.label', required=True, string="Label", help="Name of the product label")
    _sql_constraints = [('product_tmpl_id', 'unique (product_tmpl_id,website_id)',
                         'Duplicate records in label line not allowed !')]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            args = args or []
            domain = [('label', operator, name)]
            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return super(ProductLabelLine, self)._name_search(
            name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
