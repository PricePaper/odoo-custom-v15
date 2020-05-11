# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GenerateCommission(models.TransientModel):
    _name = 'generate.sales.commission'
    _description = 'Generate Sales commission'

    report_type = fields.Selection([('invoice_paid', 'Invoice Paid Orders'), ('payment_pending', 'Payment Pending Orders')], string='Calculated For', default='invoice_paid', required=True)
    salesperson_id = fields.Many2one('res.partner', string='Sales Persons', domain=[('is_sales_person', '=', True)])


    @api.multi
    def generate_commission(self):
        self.ensure_one()
        paid=False
        if self.report_type == 'invoice_paid':
            paid=True
        view_id = self.env.ref('sales_commission.view_commission_sale_grouped_tree').id
        res = {
            "type": "ir.actions.act_window",
            "name" : "Sale commission",
            "res_model": "sale.commission",
            "views": [[view_id, "tree"]],
            "context": {'group_by':['sale_person_id', 'write_date:month']},
            "domain":[['is_paid', '=', paid]],
            "target": "current",
        }
        if not self.env.user.has_group('sales_commission.group_sales_commission'):
            res['domain'].append(['sale_person_id', '=', self.env.user.partner_id.id])
        return res

GenerateCommission()
