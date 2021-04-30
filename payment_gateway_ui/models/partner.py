# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    profile_id = fields.Char('Profile Id', copy=False)
    payment_id = fields.Char('Last used payment id', copy=False)


ResPartner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
