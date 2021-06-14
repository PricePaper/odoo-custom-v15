# -*- coding: utf-8 -*-

from datetime import date
import logging
from odoo import fields, models, api


class SaleCommission(models.Model):
    _name = 'sale.commission'
    _description = 'Sale Commission'

    sale_person_id = fields.Many2one('res.partner', string='Sale Person')
    commission = fields.Float(string='Commission')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    is_paid = fields.Boolean(string='Paid', default=False)
    is_cancelled = fields.Boolean(string='Cancelled', default=False)
    invoice_type = fields.Selection(
        selection=[('out_invoice', 'Invoice'), ('out_refund', 'Refund'), ('draw', 'Weekly Draw'),
                   ('bounced_cheque', 'Cheque Bounce'), ('cancel', 'Invoice Cancelled'), ('aging', 'Commission Aging')], string='Type')
    invoice_amount = fields.Float(string='Amount')
    date_invoice = fields.Date(related='invoice_id.date_invoice', string="Invoice Date", readonly=True, store=True)
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    is_settled = fields.Boolean(string='Settled')
    is_removed = fields.Boolean(string='Removed')
    settlement_id = fields.Many2one('sale.commission.settlement', string='Settlement')
    commission_date = fields.Date('Date')
    paid_date = fields.Date('Paid Date', compute='get_invoice_paid_date', store=True)


    def correct_commission(self, partner_id=None):
        pending_ids = []
        if not len(self) and partner_id:
            self = self.search([('sale_person_id', '=', partner_id), ('invoice_id', '!=', False)])
        else:
            self = self.search([('invoice_id', '!=', False)])
        for rec in self.filtered(lambda r: r.invoice_id):
            if rec.invoice_id:
                rule = rec.invoice_id.partner_id.commission_percentage_ids.filtered(lambda r: r.sale_person_id.id == rec.sale_person_id.id)
                if rule.rule_id.based_on not in ['profit', 'profit_delivery']:
                    continue
                commission = rec.invoice_id.gross_profit * (rule.rule_id.percentage / 100)
                if rec.invoice_type == 'bounced_cheque':
                    commission = commission * -1
                    rec.write({'commission': commission})
                    if commission < 0:
                        rec.is_cancelled = True

                elif rec.invoice_type == 'aging':
                    inv = rec.invoice_id.sale_commission_ids.filtered(lambda r: r.id != rec.id)
                    if len(inv) > 1:
                        pending_ids.append(rec.id)
                        continue
                    payment_date = max([payment.payment_date for payment in rec.invoice_id.payment_ids])
                    if payment_date > rec.invoice_id.date_due:
                        extra_days = payment_date - rec.invoice_id.date_due
                        if rec.invoice_id.partner_id.company_id.commission_ageing_ids:
                            commission_ageing = rec.invoice_id.partner_id.company_id.commission_ageing_ids.filtered(
                                lambda r: r.delay_days <= extra_days.days)
                            commission_ageing = commission_ageing.sorted(key=lambda r: r.delay_days, reverse=True)
                            if commission_ageing and commission_ageing[0].reduce_percentage:
                                commission = commission_ageing[0].reduce_percentage * inv.commission / 100

                                rec.write({'commission': -commission})
                                if inv.commission < 0:
                                    inv.is_cancelled = True
                                    rec.is_cancelled = True

                else:
                    rec.invoice_id.with_context({'is_cancelled':True}).check_commission(rec)
        logging.error('============================>error ids')
        logging.error(pending_ids)
        return True

    @api.depends('is_paid')
    def get_invoice_paid_date(self):
        for rec in self:
            if rec.is_paid:
                if rec.invoice_type in ('out_invoice', 'out_refund', 'aging'):
                    payment_date_list = [payment.payment_date for payment in rec.invoice_id.payment_ids]
                    rec.paid_date = max(payment_date_list) if payment_date_list else False
                elif rec.invoice_type in ('draw', 'bounced_cheque', 'cancel'):
                    rec.paid_date = rec.commission_date
    @api.multi
    def action_commission_remove(self):
        for rec in self:
            rec.settlement_id.message_post(
                body='Commission Line removed..!!<br/><span> Source &#8594; %s </span><br/>Amount &#8594; %0.2f' % (
                rec.invoice_id.move_name, rec.commission),
                subtype_id=self.env.ref('mail.mt_note').id)
            rec.is_removed = True

    @api.multi
    def action_commission_add(self):
        for rec in self:
            rec.settlement_id.message_post(
                body='Commission Line Added..!!<br/><span> Source &#8594; %s </span><br/>Amount &#8594; %0.2f' % (
                    rec.invoice_id.move_name, rec.commission),
                subtype_id=self.env.ref('mail.mt_note').id)
            rec.is_removed = False

    @api.model
    def create_weeekly_draw(self):
        sales_persons = self.env['res.partner'].search([('is_sales_person', '=', True)])
        for sales_person in sales_persons:
            weekly_draw = sales_person.weekly_draw
            if weekly_draw and weekly_draw > 0:
                daily_amount = weekly_draw / 7
                vals = {
                    'sale_person_id': sales_person.id,
                    'commission': -daily_amount,
                    'is_paid': True,
                    'invoice_type': 'draw',
                    'commission_date': date.today(),
                    'paid_date': date.today()
                }
                self.env['sale.commission'].create(vals)


SaleCommission()

class SalesCommission(models.Model):
    _name = 'sales.commission'
    _description = 'Sales Commission'

class SalesUnpaidCommission(models.Model):
    _name = 'sales.unpaid.commission'
    _description = 'Sale Unpaid Commission'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
