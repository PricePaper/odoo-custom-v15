# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_person_ids = fields.Many2many('res.partner', related='partner_id.sales_person_ids',
                                        string='Associated Sales Persons')
    
    @api.model
    def link_sc(self, sc_line_id=False, po_line_id=False):
        sc_line = self.env['sale.order.line'].browse(sc_line_id)
        po_line = self.env['purchase.order.line'].browse(po_line_id)
        po_line.write({'sale_line_id': sc_line.id})
        po_line.move_ids.write({'sale_line_id': sc_line.id, 'is_storage_contract': True})
        po_line.invoice_lines.write({'is_storage_contract': True})
        sc_line.order_id.write({'state': 'released', 'sc_po_done': True})
        return True

    @api.model
    def correct_sc(self, order_ids=[]):
        if not order_ids:
            return
        sc_inv = 0        
        for order in self.browse(order_ids):
            line_ids = []
            order.action_storage_contract_confirm()
            for line in order.order_line:
                if line.product_uom_qty > line.product_id.qty_available:
                    line.product_uom_qty = line.product_id.qty_available
                sc_inv = line.product_uom_qty * line.product_id.standard_price
                line_ids.extend([[0,0, {                                
                                'debit': sc_inv,
                                'credit': 0,
                                'journal_id': 3,
                                'name': "Storage contract inventory transfer %s" % line.product_id.name,                                
                                'account_id': 683,
                                'date_maturity': "2021-4-30",
                            }],
                            [0,0, {                                
                                'debit': 0,
                                'credit': sc_inv,
                                'journal_id': 3,
                                'name': "Storage contract inventory transfer %s" % line.product_id.name,
                                'account_id': 687,
                                'date_maturity': "2021-4-30",
                            }],[0,0, {                                
                                'debit': 0,
                                'credit': sc_inv,
                                'journal_id': 3,
                                'name': "Storage contract cost transfer %s" % line.product_id.name,
                                'account_id': 769,
                                'date_maturity': "2021-4-30",
                            }],[0,0, {                                
                                'debit': sc_inv,
                                'credit': 0,
                                'journal_id': 3,
                                'name': "Storage contract cost transfer %s" % line.product_id.name,
                                'account_id': 29,
                                'date_maturity': "2021-4-30",
                            }],])        
            move_id = self.env['account.move'].create({
                'ref': "Storage contract imported order %s transfer" % order.name,
                'line_ids': line_ids,
                'journal_id': 3,
                'date': "2021-4-30",
                'narration': "Storage contract imported orders transfer",
            })
            move_id.post()
            order.action_release()
        return True

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

    

SaleOrder_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
