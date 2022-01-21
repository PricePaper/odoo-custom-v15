# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
import time


class AccountMove(models.Model):
    _inherit = "account.move"

    is_refund = fields.Boolean('Is Refunded', default=False, copy=False)
    transaction_id_refund = fields.Char("Refunded transaction ID", copy=False)
    invoice_origin_id = fields.Many2one('account.move', "Invoice Origin ID", copy=False)
    refund_invoice_ids = fields.One2many('account.move', 'invoice_origin_id', string="Refunded Ids")
    due_amount_gateway = fields.Float('Due', copy=False)
    transaction_id = fields.Char('Transaction ID', copy=False)
#    payment_id = fields.Char('Payment Profile ID', copy=False)#TODO already ther is a field with same name,use payment_reference field to meet this purpose
    transaction_date = fields.Datetime('Transaction Date', copy=False)
    sale_ids = fields.Many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Invoices',
                                readonly=True)
    parent_invoice_id = fields.Many2one('account.move', 'Reference Invoice', copy=False)
    correction_reason = fields.Text('Reason for Correction', copy=False)
    gateway_type = fields.Selection([], string='Payment Gateway')



    def resend_link(self):
        """
        resend the link if expired
        """
        for record in self:
            return 
