# -*- coding: utf-8 -*-
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    statement_method = fields.Selection([('email', 'Email'), ('pdf_report', 'Mail'), ('none', 'None')], default='email')

    def job_queue_mail_customer_statement(self, date_from, date_to, uid):

        # inv_domain = [
        #     ('move_type', 'in', ['out_invoice', 'in_refund']),
        #     ('partner_id', '=', self.id),
        #     ('invoice_date', '<=', date_to),
        #     ('state', 'not in', ['draft', 'cancel']),
        #     ('invoice_date_due', '<', date_to),
        # ]
        # invoices = self.env['account.move'].search(inv_domain)
        invoices = self.invoice_ids.filtered(lambda r: r.invoice_date
            and r.invoice_date_due and r.move_type in ['out_invoice', 'in_refund']
            and r.invoice_date <= date_to
            and r.invoice_date_due < date_to
            and r.state not in ['draft', 'cancel'])
        mail_template = self.env.ref('customer_statement_report.email_template_customer_statement')
        past_due = False
        if invoices:
            past_due = True

        mail_template.sudo().with_context({
            'd_from': date_from,
            'd_to': date_to,
            'subject': "Customer Statement [PAST DUE] - %s" % self.name if past_due else "Customer Statement - %s" % self.name
        }).send_mail(self.id, force_send=False, notif_layout='mail.mail_notification_light')
        _logger.info("Customer Statement Mail send for: %s.", self.name)
