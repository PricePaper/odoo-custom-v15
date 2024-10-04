# -*- coding: utf-8 -*-

from odoo import api, models, fields


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    website_name = fields.Char(string='Webiste Name')