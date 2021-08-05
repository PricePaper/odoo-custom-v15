# -*- coding: utf-8 -*-
from odoo import fields, models, api, registry,SUPERUSER_ID, _
import threading
import logging

_logger = logging.getLogger(__name__)

class CustomerStatementWizard(models.TransientModel):
    _name = 'customer.statement.wizard'
    _description = 'Customer Statement Generator'

    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    partner_ids = fields.Many2many('res.partner', string="Recipients")

    @api.model
    def default_get(self, fields):
        result = super(CustomerStatementWizard, self).default_get(fields)
        result['date_from'] = self.env.user.company_id.last_statement_date
        return result

    def mail_loop(self, customers, date_from, date_to, uid):

        with api.Environment.manage():
            with registry(self.env.cr.dbname).cursor() as new_cr:
                ctx = api.Environment(new_cr, SUPERUSER_ID, {})['res.users'].context_get()
                new_env = api.Environment(new_cr, SUPERUSER_ID, ctx)
                mail_template = new_env.ref('customer_statement_report.email_template_customer_statement')
                for p in customers:
                    try:
                        t = mail_template.sudo().with_context({
                            'd_from': date_from,
                            'd_to': date_to
                        }).send_mail(p.id, True)
                        _logger.info("Mail loop activated: %s %s %s.", threading.current_thread().name, p.id, t)
                    except Exception as e:
                        bus_message = {
                            'message': e,
                            'title': "Email Failed!!",
                            'sticky': True
                        }
                        new_env['bus.bus'].sendmany([('notify_warn_%s' % uid, bus_message)])
                        break
                else:
                    new_cr.commit()
                    bus_message = {
                        'message': 'Customer Statement successfully send to customers.',
                        'title': "Success!!",
                        'sticky': True
                    }
                    new_env['bus.bus'].sendmany([('notify_info_%s' % uid, bus_message)])

        return True

    def action_generate_statement(self):
        """
        process customer against with there invoices, payment with in a range of date.
        """
        partner_ids = self.env['account.invoice'].search([
            ('type', 'in', ['out_invoice', 'in_refund']),
            ('date_invoice', '>=', self.date_from),
            ('date_invoice', '<=', self.date_to),
            ('state', 'in', ['open', 'in_payment', 'paid'])
        ]).mapped('partner_id')

        email_customer = partner_ids.filtered(lambda p: p.statement_method == 'email')
        pdf_customer = partner_ids.filtered(lambda p: p.statement_method == 'pdf_report')
        self.env.user.company_id.write({'last_statement_date': self.date_to})
        if email_customer:
            t = threading.Thread(target=self.mail_loop, args=([email_customer, self.date_from, self.date_to, self.env.uid]))
            t.setName('CustomerStatement Email (Beta)')
            t.start()
        if pdf_customer:
            report = self.env.ref('customer_statement_report.report_customer_statement_pdf')
            return report.report_action(pdf_customer, data={
                'date_range': {
                    'd_from': self.date_from,
                    'd_to': self.date_to}
            })


