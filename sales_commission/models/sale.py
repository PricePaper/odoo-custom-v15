# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_person_ids = fields.Many2many('res.partner', related='partner_id.sales_person_ids',
                                        string='Associated Sales Persons')


SaleOrder()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
