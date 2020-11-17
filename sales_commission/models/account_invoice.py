# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sales_person_ids = fields.Many2many('res.partner', related='partner_id.sales_person_ids', string='Associated Sales Persons')


    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self:
            rec = invoice.calculate_commission()
        return res

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        for invoice in self:
            rec = invoice.calculate_commission()
            if rec and invoice.state == 'paid':
                rec.write({'is_paid': True})
                if invoice.payment_ids:
                    invoice.check_commission(rec)
                    invoice.check_due_date(rec)
        return res


    def check_commission(self, lines):
        for line in lines:
            profit = self.gross_profit
            amount = self.amount_total
            commission = line.commission
            payment_date_list = [rec.payment_date for rec in self.payment_ids]
            payment_date = max(payment_date_list) if payment_date_list else False
            if self.payment_term_id.due_days:
                days=self.payment_term_id.due_days
                if payment_date and payment_date > self.date_invoice+relativedelta(days=days):
                    profit += self.amount_total*(self.payment_term_id.discount_per/100)
            if self.payment_ids[0].payment_method_id.code == 'electronic' and self.partner_id.payment_method == 'cash':
                profit -= self.amount_total*0.03
            if self.payment_ids[0].payment_method_id.code == 'manual' and self.partner_id.payment_method == 'credit_card':
                profit += self.amount_total*0.03

            rule_id = self.partner_id.commission_percentage_ids.filtered(lambda r : r.sale_person_id == line.sale_person_id).mapped('rule_id')
            if rule_id:
                if rule_id.based_on in ['profit', 'profit_delivery']:
                    commission = profit  * (rule_id.percentage/100)
                elif rule_id.based_on =='invoice':
                    amount = self.amount_total
                    # if self.partner_id.payment_method == 'credit_card':
                    #     amount -= self.amount_total*0.03
                    # if self.payment_term_id.discount_per > 0:
                    #     amount -= self.amount_total*(self.payment_term_id.discount_per/100)
                    commission = amount * (rule_id.percentage/100)
            line.write({'commission': commission})




    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        if self._context.get('from_check_bounce', True):
            return res
        for invoice in self:
            commission_rec = self.env['sale.commission'].search([('invoice_id', '=', invoice.id)])
            commission_rec and commission_rec.unlink()
        return res

    def check_due_date(self, lines):
        """
        Apply commission Ageing by checking due date
        """

        for line in lines:
            payment_date = max([rec.payment_date for rec in self.payment_ids])
            if payment_date > self.date_due:
                extra_days = payment_date - self.date_due
                if self.partner_id.company_id.commission_ageing_ids:
                    commission_ageing = self.partner_id.company_id.commission_ageing_ids.filtered(lambda r : r.delay_days <= extra_days.days)
                    commission_ageing = commission_ageing.sorted(key=lambda r: r.delay_days, reverse=True)
                    if commission_ageing and commission_ageing[0].reduce_percentage:
                        commission = commission_ageing[0].reduce_percentage * line.commission / 100
                        vals = {
                                'sale_person_id' : line.sale_person_id.id,
                                'sale_id': line.sale_id.id,
                                'commission': -commission,
                                'invoice_id' : self.id,
                                'invoice_type' : self.type,
                                'is_paid':True,
                                'invoice_amount':self.amount_total,
                                }
                        commission_rec = self.env['sale.commission'].create(vals)



    def calculate_commission(self):

        if len(self.invoice_line_ids) == 1 and self.invoice_line_ids[0].quantity < 0:
            return False
        commission_rec = self.env['sale.commission'].search([('invoice_id', '=', self.id), ('is_paid', '=', False)])
        if not commission_rec and self.type in ['out_invoice','out_refund']:
            profit = self.gross_profit
            for rec in self.partner_id.commission_percentage_ids:
                if not rec.rule_id:
                    raise UserError(_('Commission rule is not configured for %s.' %(rec.sale_person_id.name)))
                commission = 0
                if rec.rule_id.based_on in ['profit', 'profit_delivery']:
                    commission = profit  * (rec.rule_id.percentage/100)
                elif rec.rule_id.based_on =='invoice':
                    amount = self.amount_total
                    # if self.partner_id.payment_method == 'credit_card':
                    #     amount -= self.amount_total*0.03
                    # if self.payment_term_id.discount_per > 0:
                    #     amount -= self.amount_total*(self.payment_term_id.discount_per/100)
                    commission = amount * (rec.rule_id.percentage/100)
                if self.type == 'out_refund':
                    commission = -commission
                sale = self.invoice_line_ids.mapped('sale_line_ids')
                vals = {
                        'sale_person_id' : rec.sale_person_id.id,
                        'sale_id': sale and sale[-1].order_id.id,
                        'commission': commission,
                        'invoice_id' : self.id,
                        'invoice_type' : self.type,
                        'is_paid':False,
                        'invoice_amount':self.amount_total,
                        }
                commission_rec = self.env['sale.commission'].create(vals)
        return commission_rec



AccountInvoice()
