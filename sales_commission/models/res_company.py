# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    commission_ageing_ids = fields.One2many('commission.ageing', 'company_id', string='Commission Ageing reduction percentage')
    # sale_writeoff_account_id = fields.Many2one('account.account', string='Sale Writeoff Account', domain=[('deprecated', '=', False)])



ResCompany()
