# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    product_lst_price_months = fields.Integer(string='STD price min #Months ', default=2)
    partner_count = fields.Integer(string='STD price min #partner', default=4)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
