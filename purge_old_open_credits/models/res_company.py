# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    purge_old_open_credit_limit = fields.Integer(default=120, string="Open Credit Active Days")



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    credit_purge_account = fields.Many2one('account.account',
        string='Old credit purge: Account',
        config_parameter='purge_old_open_credits.credit_purge_account')
    payment_purge_account = fields.Many2one('account.account',
        string='Old Customer Payment purge: Account',
        config_parameter='purge_old_open_credits.payment_purge_account')
    purge_old_payment_day_limit = fields.Integer(default=120, string="Open Payment Active Days",
        config_parameter='purge_old_open_credits.purge_old_payment_day_limit')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
