# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    batch_id = fields.Many2one('stock.picking.batch', string='Delivery Batch')


AccountPayment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
