# -*- coding: utf-8 -*-

from odoo import fields, models


class CommissionAgeing(models.Model):
    _name = 'commission.ageing'
    _description = 'Commission Ageing'

    delay_days = fields.Integer(string='Days +')
    reduce_percentage = fields.Float(string='Reduce commission by %')
    company_id = fields.Many2one('res.company', string='Company')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
