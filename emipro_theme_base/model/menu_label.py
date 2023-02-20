# -*- coding: utf-8 -*-
"""
    This model is used to create a menu label
"""
from odoo import api, fields, models, _


class MenuLabel(models.Model):
    """
    Class to handle menu label records
    """
    _name = "menu.label"
    _description = "Menu Label"

    name = fields.Char("Name", required=True, translate=True, help="Name of the menu label")
    label_background_color = fields.Char(
        string='Background Color',
        help="Here you can set a specific HTML color index (e.g. #ff0000) to display the "
             "menu label"
             "background color")
    label_text_color = fields.Char(
        string='Color',
        help="Here you can set a specific HTML color index (e.g. #ff0000) to display the text "
             "color of menu label.")
