# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mobile_app_sale_team = fields.Many2one('crm.team',
        string='Mobile App Sale Team',
        config_parameter='ppt_mobile_apis.mobile_app_sale_team')

    mobile_app_new_category = fields.Many2one('product.public.category',
      string='Mobile App New Arrival category',
      config_parameter='ppt_mobile_apis.mobile_app_new_category')
