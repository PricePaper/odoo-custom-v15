# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auth_start_hour = fields.Float(string='Starting Hour',
        config_parameter='authorize_extension.auth_start_hour',
        default=8.0)
