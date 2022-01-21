# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_sales_person = fields.Boolean(string='Is sale person')
    commission_percentage_ids = fields.One2many('commission.percentage', 'partner_id',
                                                string='Sales Persons Commissions')
    default_commission_rule = fields.Many2one('commission.rules', string='Default Commission Rule')
    sales_person_ids = fields.Many2many('res.partner', 'sale_per_id', 'cust_id', compute='get_sales_persons',
                                        string='Sales Persons', store=True, inverse="_inverse_set_salespersons")
    customer_ids = fields.Many2many('res.partner', 'cust_id', 'sale_per_id', string='Customers')
    weekly_draw = fields.Float(string='Weekly Draw Amount')
    last_so = fields.Char(string='Last Sale order', compute='get_last_sale_order', store=True)
    last_so_date = fields.Datetime(string='Last Sale Date', compute='get_last_sale_order', store=True)
    sales_person_code = fields.Char(string='Sale Person Code')
    payment_method = fields.Selection([('credit_card', 'Credit Card'), ('cash', 'Cash')], string='Payment Method',
                                      required=True, default='cash')

    def _inverse_set_salespersons(self):
        for partner in self:
            pass #TODO remove me 


    @api.depends('sale_order_ids.confirmation_date')
    def get_last_sale_order(self):
        for record in self:
            last_so = last_so_date = False
            if record.sale_order_ids:
                order = record.sale_order_ids.search(
                    [('partner_id', '=', record.id), ('state', 'in', ['sale', 'done'])], order='confirmation_date desc',
                    limit=1)
                if order:
                    last_so = order.name
                    last_so_date = order.confirmation_date
            record.last_so = last_so
            record.last_so_date = last_so_date

    @api.depends('commission_percentage_ids.sale_person_id')
    def get_sales_persons(self):
        for record in self:
            sales_person_ids = []
            if record.commission_percentage_ids:
                sales_persons = record.commission_percentage_ids.mapped('sale_person_id').ids
                sales_person_ids = [(6, 0, sales_persons)]
            record.sales_person_ids = sales_person_ids


    def action_view_partner_open_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'child_of', self.id),
            ('state', 'not in', ['paid', 'cancel'])
        ]
        action['context'] = {'default_move_type':'out_invoice', 'move_type':'out_invoice', 'journal_type': 'sale', 'search_default_open': 1}
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
