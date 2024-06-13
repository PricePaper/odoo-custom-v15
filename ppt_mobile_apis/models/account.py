# -*- coding: utf-8 -*-

from odoo import api, models, fields


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    payment_method = fields.Selection([('ach-debit', 'ACH-Debit')], string="Payment Method")



class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    @api.model
    def wrapper_fetch_payment_acquirer(self, acquirer_id):

        result = []
        message = {'success': False,
                   'error': False,
                   'data': False}

        if not isinstance(acquirer_id, int):
            message['error'] = "acquirer_id must be an integer"
            result.append(message)
            return result

        payment_acquirer = self.browse(acquirer_id)

        if not payment_acquirer.exists():
            message['error'] = "Payment Acquirer does not exist"
            result.append(message)
            return result

        message['data'] = payment_acquirer.sudo().read()
        message['success'] = True

        result.append(message)
        return result


