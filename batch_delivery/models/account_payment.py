# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    batch_id = fields.Many2one('stock.picking.batch', string='Delivery Batch')
    # state = fields.Selection(selection_add=[], tracking=True)
    # todo overrrided for tracking, by default tracking is added in v15
    common_batch_id = fields.Many2one('batch.payment.common', string='Delivery Batch')

    def name_get(self):
        pass
        # todo for batch payment extension we can move this method to that module

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
