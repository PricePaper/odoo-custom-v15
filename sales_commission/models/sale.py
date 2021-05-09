# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_person_ids = fields.Many2many('res.partner', related='partner_id.sales_person_ids',
                                        string='Associated Sales Persons')


SaleOrder()

class SaleOrder_line(models.Model):
    _inherit = 'sale.order.line'

    sales_person_ids = fields.Many2many('res.partner',  compute='get_sales_persons',
                                        string='Associated Sales Persons')
    @api.depends('order_id.partner_id', 'order_partner_id', 'order_partner_id.sales_person_ids')
    def get_sales_persons(self):
    	for rec in self:    		
    		rec.sales_person_ids = [(6, 0, rec.order_partner_id.sales_person_ids.ids)]
SaleOrder_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
