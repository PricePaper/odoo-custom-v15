# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    is_return_cleared = fields.Boolean('Return cleared')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
