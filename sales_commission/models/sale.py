# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_person_ids = fields.Many2many('res.partner', related='partner_id.sales_person_ids',
                                        string='Associated Sales Persons')


SaleOrder()

class SaleOrder_line(models.Model):
    _inherit = 'sale.order.line'

    sales_person_ids = fields.Many2many('res.partner',  compute='get_sales_persons', string='Associated Sales Persons', search='search_sales_persons')


    @api.depends('order_id.partner_id', 'order_partner_id', 'order_partner_id.sales_person_ids')
    def get_sales_persons(self):
        for rec in self:
            rec.sales_person_ids = [(6, 0, rec.order_partner_id.sales_person_ids.ids)]


    @api.multi
    def search_sales_persons(self, operator, value):
        commission = self.env['commission.percentage'].search([('sale_person_id', operator, value)])
        partner = commission.mapped('partner_id')
        order = self.env['sale.order']._search([('partner_id', 'in', partner.ids)])
        return[('order_id', 'in', order)]

    def link_sc(self, sc_line_id=False, po_line_id=False):
        sc_line = self.env['sale.order.line'].browse(sc_line_id)
        po_line = self.env['purchase.order.line'].browse(po_line_id)
        po_line.write({'sale_line_id': sc_line.id})
        po_line.move_ids.write({'sale_line_id': sc_line.id, 'is_storage_contract': True})
        po_line.invoice_lines.write({'is_storage_contract': True})
        sc_line.order_id.write({'state': 'released', 'sc_po_done': True})
        return True

SaleOrder_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
