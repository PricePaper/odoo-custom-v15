from odoo import models, fields, api, _
import ast
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gateway_type = fields.Selection(selection_add=[('authorize', 'Authorize.net')], string='Gateway Type')
