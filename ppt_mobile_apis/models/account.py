# -*- coding: utf-8 -*-

from odoo import api, models, fields



class PaymentMove(models.Model):
    _inherit = 'account.move'

    portal_paid_date = fields.Date(string='Paid date for Portal user', compute='_compute_portal_paid_date')

    def _compute_portal_paid_date(self):
        for rec in self:
            paid_date = False
            if rec.move_type in ('out_invoice', 'out_refund') and rec.payment_state in ('in_payment', 'paid'):
                paid_date = rec.sudo().paid_date
            rec.portal_paid_date = paid_date


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    payment_method = fields.Selection([('ach-debit', 'ACH-Debit')], string="Payment Method")



class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    # @api.model
    # def wrapper_fetch_payment_acquirer(self, acquirer_id):
    #     """
    #     no longer needed
    #     @param acquirer_id:
    #     @return:
    #     """
    #
    #     result = []
    #     message = {'success': False,
    #                'error': False,
    #                'data': False}
    #
    #     if not isinstance(acquirer_id, int):
    #         message['error'] = "acquirer_id must be an integer"
    #         result.append(message)
    #         return result
    #
    #     payment_acquirer = self.browse(acquirer_id)
    #
    #     if not payment_acquirer.exists():
    #         message['error'] = "Payment Acquirer does not exist"
    #         result.append(message)
    #         return result
    #
    #     message['data'] = payment_acquirer.sudo().read()
    #     message['success'] = True
    #
    #     result.append(message)
    #     return result
