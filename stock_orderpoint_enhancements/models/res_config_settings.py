# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    prophet_min_qty = fields.Integer('FBprophet monthly minimum sale',
       config_parameter='stock_orderpoint_enhancements.prophet_min_qty')
