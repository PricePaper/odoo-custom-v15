# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class HelpDeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    product_id = fields.Many2one('product.product', string='Product')


class HelpDeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    is_purchase_team = fields.Boolean(string='Purchase Team')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
