# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_driver_writeoff_account = fields.Boolean(string='Driver Writeoff Account',
                                                help='Check this box if this is the driver writeoff account.')


AccountAccount()


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def button_cancel(self):
        for move in self:
            if not move.journal_id.update_posted or not self.env.user.has_group('account.group_account_manager'):
                raise UserError(
                    _('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
        return super(AccountMove, self).button_cancel()


class AccountBatchPayment(models.Model):
    _name = 'account.batch.payment'
    _inherit = ['account.batch.payment', 'mail.thread']

    batch_picking_id = fields.Many2one('stock.picking.batch', compute='_compute_batch_picking_id')
    state = fields.Selection([('draft', 'New'), ('sent', 'Sent'), ('reconciled', 'Reconciled')], readonly=True,
                             default='draft', copy=False, track_visibility="onchange")

    def _compute_batch_picking_id(self):
        for rec in self:
            rec.batch_picking_id = rec.payment_ids.mapped('batch_id')


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        self.ensure_one()
        res = super(AccountPayment, self)._onchange_partner_type()
        # Set partner_id domain
        if res and res.get('domain'):
            if res.get('domain').get('partner_id'):
                res['domain']['partner_id'].append(('type', 'in', ('invoice', 'contact')))
            else:
                res['domain']['partner_id'] = [('type', 'in', ('invoice', 'contact'))]

        else:
            res = {'domain': {'partner_id': [('type', 'in', ('invoice', 'contact'))]}}
        return res

AccountPayment()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
