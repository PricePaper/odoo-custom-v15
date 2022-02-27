# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    driver_writeoff_account_id = fields.Many2one('account.account', string='Driver writeoff account')


ResCompany()
