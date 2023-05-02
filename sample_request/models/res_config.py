# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_sample = fields.Boolean(config_parameter = "sample_request.allow_sample", string='Allow Sample Requests',default='False')
    max_sample = fields.Integer(config_parameter = "sample_request.max_sample", string='Maximum Sample Request per Customer',default = 2)
    allow_repeat = fields.Boolean(config_parameter = "sample_request.allow_repeat", string='Allow Repeat Sample',default='False')
    allow_guest = fields.Boolean(config_parameter = "sample_request.allow_guest", string='Allow Public user to request for samples',Default=False)
    request_months = fields.Integer(config_parameter = "sample_request.request_months",string='Limit Months')
    sample_route = fields.Many2one('stock.location.route',config_parameter = "sample_request.sample_route",string='Sample Route')
