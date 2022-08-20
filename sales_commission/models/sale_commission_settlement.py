# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class SaleCommissionSettlement(models.Model):
    _name = 'sale.commission.settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sale Commission Settlement'

    name = fields.Char('Name', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]},
                       index=True, default=lambda self: _('New'))
    sales_person_id = fields.Many2one('res.partner', string='Sales Person', required=True, readonly=True,
                                      states={'draft': [('readonly', False)]})
    amount_paid = fields.Float(string="Amount", compute='_compute_total_amount', store=True)
    commission_ids = fields.One2many('sale.commission', 'settlement_id', string="Commission Lines", required=True)
    date_from = fields.Date(string="Date From", readonly=True, required=False, states={'draft': [('readonly', False)]})
    date_to = fields.Date(string="Date Upto", readonly=True, required=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], copy=False, string='Status', tracking=True, default='draft')

    @api.depends('commission_ids.commission', 'commission_ids.is_removed')
    def _compute_total_amount(self):
        for rec in self:
            rec.amount_paid = sum(rec.commission_ids.filtered(lambda rec: not rec.is_removed).mapped('commission'))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission.settlement') or _('New')
        result = super(SaleCommissionSettlement, self).create(vals)
        return result


    def action_load(self):
        for rec in self:
            domain = []
            rec.commission_ids = False
            commission_lines = self.env['sale.commission']
            if rec.sales_person_id:
                domain.append(('sale_person_id', '=', rec.sales_person_id.id))
            if rec.date_from:
                domain.append(('paid_date', '>=', rec.date_from))
            if rec.date_to:
                domain.append(('paid_date', '<=', rec.date_to))
            if domain:
                domain.extend([('is_paid', '=', True), ('is_settled', '=', False), ('is_removed', '=', False)])
                commission_lines = self.env['sale.commission'].search(domain)
            commission_lines -= self.search([]).mapped('commission_ids').filtered(
                lambda rec: not rec.is_removed and rec.is_settled)
            rec.commission_ids = commission_lines


    def action_make_payment(self):
        for rec in self:
            rec.commission_ids.filtered(lambda rec: not rec.is_removed).write({'is_settled': True, 'settlement_date':fields.Date.today()})
            rec.state = 'paid'


    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'


    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            rec.commission_ids.write({'is_settled': False})
            rec.commission_ids = False


    def action_draft(self):
        for rec in self:
            rec.state = 'draft'


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
