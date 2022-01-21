# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    # TODO Remove this field and add an account in company, change the stock_picking_batch.py
    is_driver_writeoff_account = fields.Boolean(string='Driver Writeoff Account', help='Check this box if this is the driver writeoff account.')


AccountAccount()


class AccountBatchPayment(models.Model):
    _name = 'account.batch.payment'
    _inherit = ['account.batch.payment', 'mail.thread']

    batch_picking_id = fields.Many2one('stock.picking.batch', compute='_compute_batch_picking_id', search='_search_batch_picking')
    state = fields.Selection([
        ('draft', 'New'),
        ('sent', 'Sent'),
        ('reconciled', 'Reconciled'),
    ], store=True, compute='_compute_state', default='draft',  tracking=True)

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
# todo we can add this domain in form view this method is not using
# lass AccountPayment(models.Model):
#     _inherit = 'account.payment'
#
#
#     @api.onchange('partner_type')
#     def _onchange_partner_type(self):
#         self.ensure_one()
#         res = super(AccountPayment, self)._onchange_partner_type()
#         # Set partner_id domain
#         if res and res.get('domain'):
#             if res.get('domain').get('partner_id'):
#                 res['domain']['partner_id'].append(('type', 'in', ('invoice', 'contact')))
#             else:
#                 res['domain']['partner_id'] = [('type', 'in', ('invoice', 'contact'))]
#
#         else:
#             res = {'domain': {'partner_id': [('type', 'in', ('invoice', 'contact'))]}}
#         return res
#
# AccountPayment()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
