from odoo import fields, models, api, _
from odoo.exceptions import UserError

class Website(models.Model):
    _inherit='website'
    helpdesk_team_website = fields.Many2one('helpdesk.team')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    helpdesk_team_website = fields.Many2one('helpdesk.team', related='website_id.helpdesk_team_website', readonly=False)
