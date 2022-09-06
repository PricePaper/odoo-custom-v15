# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    is_tax_exempt = fields.Boolean('Is Tax Exempt?')


AccountFiscalPosition()
