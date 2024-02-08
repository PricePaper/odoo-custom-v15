# -*- coding: utf-8 -*-
"""
    This model is used to create a slider filter fields
"""
from odoo import fields, models


class SliderFilter(models.Model):
    _name = "slider.filter"
    _description = "Slider Filter"

    display_name = fields.Char(string="Name", required=True, translate=True)
    website_published = fields.Boolean(string='Website Publish', default=True)
    filter_domain = fields.Text(string="Filter Domain", required=True)

    def website_publish_button(self):
        """
        Set slider filter published and unpublished on website
        :return:
        """
        self.write({'website_published': not self.website_published})
