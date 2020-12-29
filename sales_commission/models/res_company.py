# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    commission_ageing_ids = fields.One2many('commission.ageing', 'company_id',
                                            string='Commission Ageing reduction percentage')


ResCompany()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
