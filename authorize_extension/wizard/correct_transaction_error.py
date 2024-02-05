# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from ..authorize_request_custom import AuthorizeAPICustom
from odoo.exceptions import UserError


class AddInvoiceTransaction(models.TransientModel):
    _name = "correct.transaction.error"

    acquirer_reference = fields.Char('Transaction ref')

    def check_transaction_error(self):

        transaction = self.env['payment.transaction'].browse(self._context.get('active_id'))

        txs = self.env['payment.transaction'].search([('acquirer_reference', '=',  self.acquirer_reference)])
        if txs:
            raise UserError("%s has the same reference." %(txs.reference))

        authorize_api = AuthorizeAPICustom(transaction.acquirer_id)
        res_content = authorize_api.get_transaction_detail(self.acquirer_reference)

        result = res_content.get('messages', {}).get('resultCode', False)
        if result and result == 'Ok':
            amount = res_content.get('transaction', {}).get('authAmount', 0)
            customer_profile = res_content.get('transaction', {}).get('profile', {}).get('customerProfileId', False)
            payment_profile = res_content.get('transaction', {}).get('profile', {}).get('customerPaymentProfileId', False)

            if amount != transaction.amount:
                raise UserError("There is mismatch in amount. API amount is %s" %(amount))
            if customer_profile != transaction.token_id.authorize_profile:
                raise UserError("There is mismatch in profile ID. API profile ID is is %s" %(customer_profile))
            if payment_profile != transaction.token_id.acquirer_ref:
                raise UserError("There is mismatch in Pyment Profile ID. API Payment profile ID is is %s" %(payment_profile))


            picking = transaction.sale_order_ids.picking_ids.filtered(lambda r: r.is_payment_hold)
            status = res_content.get('transaction', {}).get('transactionStatus', '')
            if status == 'authorizedPendingCapture':
                transaction.state = 'authorized'
                transaction.acquirer_reference = self.acquirer_reference

                if transaction.sale_order_ids.filtered(lambda r: r.is_transaction_pending):
                    transaction.sale_order_ids.filtered(lambda r: r.is_transaction_pending).write({'is_transaction_pending': False, 'hold_state': 'release'})
                if picking:
                    picking.write({'is_payment_hold': False})
            elif status in ('settledSuccessfully', 'refundSettledSuccessfully', 'capturedPendingSettlement', 'refundPendingSettlement'):
                if picking:
                    picking.write({'is_payment_hold': False})
                    transaction.sale_order_ids.write({'is_transaction_pending': False, 'hold_state': 'release'})
                transaction._create_payment()
                transaction.state = 'done'
        else:
            raise UserError("Can not find any transaction with the given reference")
