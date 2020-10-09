# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class SaleCommission(models.Model):
    _name = 'sale.commission'
    _description = 'Sale Commission'

    sale_person_id = fields.Many2one('res.partner', string='Sale Person')
    commission = fields.Float(string='Commission')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    is_paid = fields.Boolean(string='Paid')
    invoice_type = fields.Selection(selection=[('out_invoice', 'Invoice'), ('out_refund', 'Refund')], string='Invoice Type')
    invoice_amount = fields.Float(string='Amount')
    date_invoice = fields.Date(related='invoice_id.date_invoice', string="Invoice Date", readonly=True, store=True)
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    is_settled = fields.Boolean(string='Settled')
    is_removed = fields.Boolean(string='Removed')
    settlement_id = fields.Many2one('sale.commission.settlement', string='Settlement')

    @api.multi
    def action_commission_remove(self):
        for rec in self:
            rec.settlement_id.message_post(
            body='Commission Line removed..!!<br/><span> Source &#8594; %s </span><br/>Amount &#8594; %0.2f' % (rec.invoice_id.move_name, rec.commission),
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



SaleCommission()
