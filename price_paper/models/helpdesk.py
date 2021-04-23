# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class HelpDeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    is_sales_team = fields.Boolean(string='Sales Team')
    is_credit_team = fields.Boolean(string='Sales Team')

HelpDeskTeam()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
