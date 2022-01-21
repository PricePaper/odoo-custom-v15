# -*- coding: utf-8 -*-

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    sales_person_ids = fields.Many2many('res.partner', string='Associated Sales Persons')
    check_bounce_invoice = fields.Boolean(string='Check Bounce Invoice', default=False)
    sale_commission_ids = fields.One2many('sale.commission', 'invoice_id', string='Commission')
    paid_date = fields.Date(string='Paid_date', compute='_compute_paid_date')
    commission_rule_ids = fields.Many2many('commission.rules', string='Commission Rules')

    def _compute_paid_date(self):
        for rec in self:
            paid_date = False
            if rec.state == 'paid':
                paid_date_list = rec.payment_move_line_ids.mapped('date')
                if paid_date_list:
                    paid_date = max(paid_date_list)
            rec.paid_date = paid_date
 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
