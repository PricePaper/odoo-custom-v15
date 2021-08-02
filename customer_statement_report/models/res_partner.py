# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    statement_method = fields.Selection([('email', 'Email'), ('pdf_report', 'Pdf')], default='email')
