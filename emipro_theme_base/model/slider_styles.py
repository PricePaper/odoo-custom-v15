# -*- coding: utf-8 -*-
"""
    This model is used to create a slider styles fields
"""
from odoo import fields, models


class SliderStyles(models.Model):

    _name = "slider.styles"
    _description = "Slider Styles"

    display_name = fields.Char(string='Name', required=True)
    style_template_key = fields.Char(string='Key', required=True)
    slider_type = fields.Selection([('product', 'Product'), ('category', 'Product Category'),
                                    ('brand', 'Product Brand')], string="Slider Type", required=True,
                                   default='product', readonly=False)
    slider_style = fields.Selection([('slider', 'Slider'), ('grid', 'grid'), ('list', 'List'), ('custom', 'Custom')],
                                    string="Slider Style", required=True, default='slider', readonly=False)
