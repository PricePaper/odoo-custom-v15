# -*- coding: utf-8 -*-
from odoo import api, models, fields, _




class ResPartner(models.Model):
    _inherit = "res.partner"

    sample_request_limit  = fields.Integer(string='Sample Request Limit',default=0)
