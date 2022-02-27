# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountBatchPayment(models.Model):
    _name = 'account.batch.payment'
    _inherit = ['account.batch.payment', 'mail.thread']

    batch_picking_id = fields.Many2one('stock.picking.batch', compute='_compute_batch_picking_id', search='_search_batch_picking')
    state = fields.Selection([
        ('draft', 'New'),
        ('sent', 'Sent'),
        ('reconciled', 'Reconciled'),
    ], store=True, compute='_compute_state', default='draft', tracking=True)

    @api.depends('payment_ids.move_id.is_move_sent', 'payment_ids.is_matched')
    def _compute_state(self):
        return super()._compute_state()

    def _compute_batch_picking_id(self):
        for rec in self:
            rec.batch_picking_id = rec.payment_ids.mapped('batch_id')

    @api.model
    def _search_batch_picking(self, operator, value):
        payments = self.env['account.payment'].search([('batch_id.name', operator, value)])
        account_batch = self.env['account.batch.payment'].search([('payment_ids', 'in', payments.ids)])
        return [('id', 'in', account_batch.ids)]


AccountBatchPayment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
