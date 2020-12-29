# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CommissionPercentage(models.Model):
    _name = 'commission.percentage'
    _description = 'Commission Percentage'

    sale_person_id = fields.Many2one('res.partner', string='Sales Person', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, ondelete='cascade')
    rule_id = fields.Many2one('commission.rules', string='Rule', required=True)

    @api.onchange('sale_person_id')
    def sale_person_id_change(self):
        if self.sale_person_id:
            self.rule_id = self.sale_person_id.default_commission_rule

    @api.one
    @api.constrains('sale_person_id', 'partner_id')
    def check_duplicates(self):
        result = self.search([('sale_person_id', '=', self.sale_person_id.id), ('partner_id', '=', self.partner_id.id),
                              ('id', '!=', self.id)])
        if result:
            raise ValidationError('Combination of sales_person_id and partner_id must be unique')


CommissionPercentage()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
