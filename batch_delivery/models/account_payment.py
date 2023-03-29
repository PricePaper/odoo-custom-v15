# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    batch_id = fields.Many2one('stock.picking.batch', string='Delivery Batch')
    common_batch_id = fields.Many2one('batch.payment.common', string='Delivery Batch')

    def name_get(self):
        result = []
        if self._context.get('from_return_check_process', False):
            for payment in self:
                result.append((payment.id, '%s ( %s )' % (payment.name, payment.amount)))
            return result
        return super(AccountPayment, self).name_get()


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    payment_fee = fields.Float('Payment Charge %')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
