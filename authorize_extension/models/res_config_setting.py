# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auth_start_hour = fields.Float(
        string='Starting Hour',
        config_parameter='authorize_extension.auth_start_hour',
        default=8.0)
    card_fee = fields.Float(
        string='Credit Card Fee Percentage',
        config_parameter='authorize_extension.card_fee',
        default=3.0)
    transaction_fee_account_id = fields.Many2one(
        'account.account',
        config_parameter='authorize_extension.transaction_fee_account',
        domain=[('deprecated', '=', False)],
        string="Transaction fee account"
    )
    transaction_fee_journal_id = fields.Many2one(
        'account.journal',
        config_parameter='authorize_extension.transaction_fee_journal_id',
        string="Transaction fee Journal"
    )
