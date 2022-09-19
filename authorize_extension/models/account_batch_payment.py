# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    def create_autherize_batch_payment(self):

        auth_journals = self.env['account.journal'].search([('is_autherize_net', '=', True)])
        today = date.today()
        time = self.env['ir.config_parameter'].sudo().get_param('authorize_extension.auth_start_hour')

        hour, minute = time.split('.')
        minute = float('0.' + minute)
        minute = str(round( minute * 60, 2)).split('.')[0]
        start_date = "%s-%s-%s %s:%s:%s" % (today.year , today.month, today.day-1, hour, minute, 00)
        end_date = "%s-%s-%s %s:%s:%s" % (today.year , today.month, today.day, hour, minute, 00)
        start_date = datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT)
        end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATETIME_FORMAT)

        payments = self.env['account.payment'].search([('journal_id', 'in', auth_journals.ids),
                ('state', '=', 'posted'),
                ('create_date', '>', start_date),
                ('create_date', '<', end_date),
                ('batch_payment_id', '=', False)])
        if payments:
            journals = payments.mapped('journal_id')
            payment_methods = payments.mapped('payment_method_line_id')
            for journal in journals:
                for p_method in payment_methods:
                    filtered_payments = payments.filtered(lambda r: r.journal_id == journal and r.payment_method_line_id == p_method)
                    if filtered_payments:
                        batch_id = self.env['account.batch.payment'].create({
                            'batch_type': 'inbound',
                            'journal_id': journal.id,
                            'payment_method_line_id': p_method.id,
                            })
                        filtered_payments.write({'batch_payment_id': batch_id.id})



AccountBatchPayment()
