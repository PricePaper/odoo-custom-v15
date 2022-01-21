# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api,_


class CommissionRules(models.Model):
    _name = 'commission.rules'
    _description = 'Commission Rules'

    sales_person_id = fields.Many2one('res.partner', string='Sales Persons', required=True)
    based_on = fields.Selection(selection=[('profit', 'Profit'), ('invoice', 'Paid Invoice'), ('profit_delivery', 'Profit After Delivery')], string='Based on', required=True)
    percentage = fields.Float(string='Percentage', required=True)


    @api.depends('based_on', 'percentage')
    def name_get(self):
        result = []
        for record in self:
            name = "%s_%s" % (record.based_on and record.based_on or '', record.percentage and record.percentage or '')
            result.append((record.id,name))
        return result



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
