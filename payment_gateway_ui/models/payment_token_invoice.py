# -*- coding: utf-8 -*-

from odoo import models, fields, api
import hashlib
from datetime import datetime


class PaymentTokenInvoice(models.Model):
    _name = 'payment.token.invoice'

    token = fields.Char("Payment token", size=128, help="Unique identifier for retrieving an EDI document.")
    invoice_id = fields.Many2one('account.invoice')
    order_id = fields.Many2one('sale.order', string="Order")
    state = fields.Selection(
        [('draft', 'Not Visited Yet'), ('visited', 'Visited'), ('submitted', 'Submitted'), ('paid', 'Payed'),
         ('expired', 'Expired'), ('error', 'Error')], string='Visitor Status', default='draft', readonly=True)
    model = fields.Selection(
        [('sale', 'Sale'), ('invoice', 'Invoice')], string='Model', readonly=True)

    def get_authorization_document(self, token):
        """
            returns a record with current token
        """
        if token:
            return self.search([('token', '=', token)], limit=1)
        return False

    def edi_token_recreate(self, model_id, model):
        db_uuid = self.env['ir.config_parameter'].get_param('database.uuid')
        if model == 'invoice':
            srch_array = [('model', '=', 'invoice'), ('invoice_id', '=', model_id.id)]
        else:
            srch_array = [('model', '=', 'sale'), ('order_id', '=', model_id.id)]
        record = self.search(srch_array, limit=1)
        if record:
            token = hashlib.sha256((u'%s-%s-%s' % (db_uuid, model_id.name, datetime.now())).encode('utf-8')).hexdigest()
            return record.write({'token': token, 'state': 'draft', 'model': model})
        else:
            return self.create_authorization_token_invoice(model_id, model)

    def create_authorization_token_invoice(self, model_id, model):
        """
                create a record with payment token,order,invoice
        """
        if model == 'invoice':
            srch_array = [('model', '=', 'invoice'), ('invoice_id', '=', model_id.id)]
        else:
            srch_array = [('model', '=', 'sale'), ('order_id', '=', model_id.id)]
        record = self.search(srch_array, limit=1)
        if record:
            return record
        else:
            db_uuid = self.env['ir.config_parameter'].get_param('database.uuid')
            token = hashlib.sha256((u'%s-%s-%s' % (db_uuid, model_id.name, datetime.now())).encode('utf-8')).hexdigest()
            if model == 'invoice':
                return self.create({'token': token, 'invoice_id': model_id.id, 'model': model})
            else:
                return self.create({'token': token, 'order_id': model_id.id, 'model': model})

    def get_invoice_payment_record(self, model_id, model):
        """
                returns a  stored payment record of current invoice.
        """

        if model == 'invoice':
            srch_array = [('model', '=', 'invoice'), ('invoice_id', '=', model_id.id)]
        else:
            srch_array = [('model', '=', 'sale'), ('order_id', '=', model_id.id)]
        record = self.search(srch_array, limit=1)
        if record:
            return record.token
        else:
            self.create_authorization_token_invoice(model_id, model)
            record = self.search(srch_array, limit=1)
            return record.token

    def create_authorization_token(self, order, invoice, model):
        """
                create a record with payment token,order,invoice
        """
        db_uuid = self.env['ir.config_parameter'].get_param('database.uuid')
        token = hashlib.sha256((u'%s-%s-%s' % (db_uuid, order.name, datetime.now())).encode('utf-8')).hexdigest()
        return self.create(
            {'token': token, 'order_id': order.id, 'invoice_id': invoice.id, 'model': 'sale'})