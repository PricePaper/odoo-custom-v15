# -*- coding: utf-8 -*-

from odoo import models, fields, api
import csv
import logging

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_person_ids = fields.Many2many('res.partner', string='Associated Sales Persons')
    commission_rule_ids = fields.Many2many('commission.rules', string='Commission Rules')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id and self.partner_id.sales_person_ids:
            self.sales_person_ids = self.partner_id.sales_person_ids.filtered(lambda r: r.active)
        else:
            self.sales_person_ids = False
        return res

    @api.onchange('sales_person_ids')
    def onchange_sales_person_ids(self):
        if self.sales_person_ids:
            rules = self.partner_id.mapped('commission_percentage_ids').filtered(lambda r:r.sale_person_id in self.sales_person_ids).mapped('rule_id')
            if rules:
                sale_rep = rules.mapped('sales_person_id')
                non_sale_rep = self.sales_person_ids - sale_rep
                for rep in non_sale_rep:
                    rules |= rep.default_commission_rule
            else:
                for rep in self.sales_person_ids:
                    rules |= rep.mapped('default_commission_rule')
            self.commission_rule_ids = rules
        else:
            self.commission_rule_ids = False

    def _prepare_invoice(self):
        """
        Override to add sale person, commission rules
        """
        res = super(SaleOrder, self)._prepare_invoice()
        if self.sales_person_ids:
            res.update({
                'sales_person_ids': [(6, 0, self.sales_person_ids.ids)]
            })
        if self.commission_rule_ids:
            res.update({
                'commission_rule_ids': [(6, 0, self.commission_rule_ids.ids)]
            })
        return res



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

    @api.depends('order_line.profit_margin')
    def calculate_gross_profit(self):
        """
        If payment metod of customer is credit card
        reduce 3percentage of amount from the profit.
        """
        for order in self:
            gross_profit = sum([line.profit_margin for line in order.order_line])
            if order.partner_id.payment_method == 'credit_card':
                gross_profit -= order.amount_total * 0.03
            if order.payment_term_id.discount_per > 0:
                gross_profit -= order.amount_total * (order.payment_term_id.discount_per / 100)
            order.update({'gross_profit': round(gross_profit, 2)})



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
