# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_autherize_net = fields.Boolean('Is Authorize.net Journal', default=False)
    is_transaction_fee = fields.Boolean('Is transaction fee journal', default=False)

    @api.constrains('is_transaction_fee')
    def transaction_fee_duplicate(self):
        for record in self:
            if record.is_transaction_fee and self.search_count([('is_transaction_fee', '=', True), ('id', '!=', record.id)]):
                raise ValidationError("cannot have multiple transaction fee journal")
