# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_autherize_net = fields.Boolean('Is Authorize.net Journal', default=False)
