# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    amount_a = fields.Integer(string='Amount for Ranking A')
    amount_b = fields.Integer(string='Amount for Ranking B')
    amount_c = fields.Integer(string='Amount for Ranking C')
    amount_d = fields.Integer(string='Amount for Ranking D')
    amount_e = fields.Integer(string='Amount for Ranking E')
    amount_f = fields.Integer(string='Amount for Ranking F')


ResCompany()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
