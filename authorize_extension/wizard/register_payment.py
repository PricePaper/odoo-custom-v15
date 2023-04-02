# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):

        res = super(AccountPaymentRegister, self).action_create_payments()

        invoices = self.env['account.move'].browse(self._context.get('active_ids'))
        if any(invoices.mapped('is_authorize_tx_failed')):
            view_id = self.env.ref('price_paper.view_sale_warning_wizard').id
            return {
                'name': 'Transaction Error',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.warning.wizard',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'context': {'default_warning_message': '\n'.join(['Payment Transaction Failed.please check invoice log'])},
                'target': 'new'
            }

        return res

    def _create_payments(self):
        """
        override to send mail
        """
        res = super()._create_payments()
        if self.transaction_fee:
            for payment in res:
                if payment.payment_transaction_id:
                    payment.payment_transaction_id.send_receipt_mail()
        return res
