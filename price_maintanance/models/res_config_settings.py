# -*- coding: utf-8 -*-


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cost_change_email_ids = fields.Char('Emails for cost change report', config_parameter='purchase.cost_change_email_ids')

