# -*- coding: utf-8 -*-

from odoo import models, fields, api
import csv
import logging

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_person_ids = fields.Many2many('res.partner', string='Associated Sales Persons')
    commission_rule_ids = fields.Many2many('commission.rules', string='Commission Rules')



class SaleOrder_line(models.Model):
    _inherit = 'sale.order.line'

    sales_person_ids = fields.Many2many('res.partner',  compute='get_sales_persons', string='Associated Sales Persons', search='search_sales_persons')


    @api.depends('order_id.sales_person_ids')
    def get_sales_persons(self):
        for rec in self:
            rec.sales_person_ids = [(6, 0, rec.order_id.sales_person_ids.ids)]

    def search_sales_persons(self, operator, value):
        commission = self.env['commission.percentage'].search([('sale_person_id', operator, value)])
        partner = commission.mapped('partner_id')
        order = self.env['sale.order']._search([('partner_id', 'in', partner.ids)])
        return [('order_id', 'in', order)]



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
