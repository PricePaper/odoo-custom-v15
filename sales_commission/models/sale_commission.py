# -*- coding: utf-8 -*-

from datetime import date
import logging
from odoo import fields, models, api
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import float_round


class SaleCommission(models.Model):
    _name = 'sale.commission'
    _description = 'Sale Commission'

    sale_person_id = fields.Many2one('res.partner', string='Sale Person')
    commission = fields.Float(string='Commission', digits='Product Price')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    is_paid = fields.Boolean(string='Paid', default=False)
    is_cancelled = fields.Boolean(string='Cancelled', default=False)
    invoice_type = fields.Selection(
        selection=[('out_invoice', 'Invoice'), ('out_refund', 'Refund'), ('draw', 'Weekly Draw'),
                   ('bounced_cheque', 'Cheque Bounce'), ('cancel', 'Invoice Cancelled'),
                   ('aging', 'Commission Aging'), ('unreconcile', 'Invoice Unreconciled'),
                   ('bounced_reverse', 'Cheque Bounce Reverse')], string='Type')
    invoice_amount = fields.Float(string='Amount')
    date_invoice = fields.Date(related='invoice_id.invoice_date', string="Invoice Date", readonly=True, store=True)
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    is_settled = fields.Boolean(string='Settled')
    is_removed = fields.Boolean(string='Removed')
    settlement_id = fields.Many2one('sale.commission.settlement', string='Settlement')
    commission_date = fields.Date('Date')
    paid_date = fields.Date('Paid Date', compute='get_invoice_paid_date', store=True)
    partner_id = fields.Many2one(related='invoice_id.partner_id', string="Customer")

    @api.depends('is_paid')
    def get_invoice_paid_date(self):
        for rec in self:
            paid_date = False
            if rec.is_paid:
                if rec.invoice_type in ('out_invoice', 'out_refund', 'aging'):
                    paid_date = rec.invoice_id.paid_date and rec.invoice_id.paid_date
                elif rec.invoice_type in ('draw', 'bounced_cheque', 'cancel', 'unreconcile'):
                    paid_date = rec.commission_date
            rec.paid_date = paid_date



    def action_commission_add(self):
        for rec in self:
            rec.settlement_id.message_post(
                body='Commission Line Added..!!<br/><span> Source &#8594; %s </span><br/>Amount &#8594; %0.2f' % (
                    rec.invoice_id.move_name, rec.commission),
                subtype_id=self.env.ref('mail.mt_note').id)
            rec.is_removed = False


    def action_commission_remove(self):
        for rec in self:
            rec.settlement_id.message_post(
                body='Commission Line removed..!!<br/><span> Source &#8594; %s </span><br/>Amount &#8594; %0.2f' % (
                rec.invoice_id.move_name, rec.commission),
                subtype_id=self.env.ref('mail.mt_note').id)
            rec.is_removed = True




#class SalesCommission(models.Model):
#    _name = 'sales.commission'
#    _description = 'Sales Commission'

#class SalesUnpaidCommission(models.Model):
#    _name = 'sales.unpaid.commission'
#    _description = 'Sale Unpaid Commission'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
