# coding: utf-8
from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    nacha_company_chase_account = fields.Char(help="This is your Chase funding account number",
                                              string="Company Discretionary Data")
