# -*- coding: utf-8 -*-

"""
    This model is used to create a html field.
"""

from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    is_category_page = fields.Boolean(string='Allow Category Page',
                                      help="It will set the separate page for this category")
    category_page = fields.Many2one("website.page", string="Select Page",
                                    help="Select the page which you want to set for this category.")
    icon = fields.Binary('Category Icon')
    menu_label_id = fields.Many2one(
        'menu.label',
        string='Menu Label',
        help='Select a menu label for this category'
    )
