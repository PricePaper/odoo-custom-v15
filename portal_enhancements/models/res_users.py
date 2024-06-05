# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning


class ResUsers(models.Model):
    _inherit = 'res.users'

    portal_child_ids = fields.Many2many('res.partner', 'portal_user_partner_rel', 'portal_parent_user_id', 'portal_child_partner_id',
                                          string="Portal Child Users")
