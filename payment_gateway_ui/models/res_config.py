from odoo import models, fields, api, _
import ast
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gateway_type = fields.Selection([], 'Gateway Type')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        gateway_type = self.env['ir.config_parameter'].sudo().get_param('gateway_type')
        res.update(
            gateway_type=gateway_type,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('gateway_type', self.gateway_type)
