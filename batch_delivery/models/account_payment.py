# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    batch_id = fields.Many2one('stock.picking.batch', string='Delivery Batch')

    @api.multi
    def print_checks(self):
        self.set_check_amount_in_words()
        return super(AccountPayment, self).print_checks()


AccountPayment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
