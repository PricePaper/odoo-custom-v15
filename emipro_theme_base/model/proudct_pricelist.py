# -*- coding: utf-8 -*-
"""
    This model is used to create a offer timer fields in pricelist
"""

from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    offer_msg = fields.Char(string="Offer Message", translate=True,
                            help="To set the message in the product offer timer.", size=35)
    is_display_timer = fields.Boolean(string='Display Timer', help="It shows the product timer on product page.")
