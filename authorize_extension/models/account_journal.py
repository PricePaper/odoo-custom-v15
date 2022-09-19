# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_autherize_net = fields.Boolean('Is Autherize.net Journal', default=False)
