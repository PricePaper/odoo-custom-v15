# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from ..authorize_request_custom import AuthorizeAPICustom
from odoo.exceptions import ValidationError


class AddInvoiceTransaction(models.TransientModel):
    _name = "add.invoice.transaction"

    transaction_ref = fields.Char('Transaction ref')

    def add_transaction(self):
        invoice = self.env['account.move'].browse(self._context.get('active_id'))

        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'authorize')])
        authorize_api = AuthorizeAPICustom(acquirer[0])
        res_content = authorize_api.get_transaction_detail(self.transaction_ref)

        if res_content.get('err_code', ''):
            raise ValidationError(_("Error: %s"%(res_content.get('err_msg', ''))))
        elif res_content.get('transaction', ''):
            invoice.an_transaction_ref = self.transaction_ref
