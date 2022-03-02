# -*- coding: utf-8 -*-
from odoo import fields, models, api, registry, SUPERUSER_ID, _
from odoo.exceptions import UserError
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

    def mail_loop(self, invoices, customers, date_from, date_to, uid):

        with self.pool.cursor() as new_cr:
            self = self.with_env(self.env(cr=new_cr))
            mail_template = self.env.ref('customer_statement_report.email_template_customer_statement')

            for p in customers:
                try:
                    past_due = False
                    if invoices.filtered(lambda inv: inv.partner_id.id == p.id and inv.invoice_date_due < fields.Date.today()):
                        past_due = True

                    t = mail_template.sudo().with_context({
                        'd_from': date_from,
                        'd_to': date_to,
                        'past_due': past_due,
                        'subject': "Customer Statement [PAST DUE] - %s" % p.name if past_due else "Customer Statement - %s" % p.name
                    }).send_mail(p.id, force_send=False, notif_layout='mail.mail_notification_light')
                    _logger.info("Mail loop activated: %s %s %s.", threading.current_thread().name, p.id, t)
                except Exception as e:
                    bus_message = {
                        'message': e,
                        'title': "Email Failed!!",
                        'sticky': True,
                        'warning': True,
                    }
                    self.env['bus.bus']._sendone(self.env.user.partner_id, 'notify_warn_%s' % uid, bus_message)
                    break
            else:
                new_cr.commit()

                bus_message = {
                    'message': 'Customer Statement successfully send to customers.',
                    'title': "Success!!",
                    'sticky': True,
                    'warning': True,
                }
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'notify_info_%s' % uid, bus_message)

        return True

    def action_generate_statement(self):
        """
        process customer against with there invoices, payment with in a range of date.
        """
        inv_domain = [
            ('move_type', 'in', ['out_invoice', 'in_refund']),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', 'not in', ['draft', 'cancel'])
        ]

        payment_domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '!=', 'cancel')
        ]

        if self._context.get('ppt_active_recipient'):
            active_ids = self._context.get('active_ids')
            inv_domain.append(('partner_id', 'in', active_ids))
            payment_domain.append(('partner_id', 'in', active_ids))

        invoices = self.env['account.move'].search(inv_domain)
        invoices_open_with_credit = invoices.filtered(
            lambda r: r.invoice_has_outstanding and r.state in ['posted'] and r.payment_state in ['not_paid', 'partial'])
        invoices_paid = invoices.filtered(lambda r: r.payment_state in ('paid', 'in_payment'))

        payment = self.env['account.payment'].search(payment_domain)
        partners = self.env['res.partner']
        if invoices_open_with_credit or invoices_paid or payment:
            partners |= (invoices_open_with_credit | invoices_paid).mapped('partner_id')
            partners |= payment.mapped('partner_id')

        partners = partners.filtered(lambda p: p.credit > 0)
        email_customer = partners.filtered(lambda p: p.statement_method == 'email')
        pdf_customer = partners.filtered(lambda p: p.statement_method == 'pdf_report')

        if not email_customer and not pdf_customer:
            raise UserError(_('Nothing to process!!'))

        self.env.user.company_id.write({'last_statement_date': self.date_to})
        if email_customer:
            if self._context.get('ppt_active_recipient'):
                past_due = False
                if invoices.filtered(lambda inv: inv.partner_id.id == email_customer.id and inv.invoice_date_due < fields.Date.today()):
                    past_due = True
                template_id = self.env.ref('customer_statement_report.email_template_customer_statement')
                compose_form_id = self.env.ref('mail.email_compose_message_wizard_form')
                ctx = {
                    'default_model': 'res.partner',
                    'default_res_id': self._context.get('active_id'),
                    'default_use_template': bool(template_id.id),
                    'default_template_id': template_id.id,
                    'default_composition_mode': 'comment',
                    'custom_layout': 'mail.mail_notification_light',
                    'force_email': False,
                    'd_from': self.date_from,
                    'd_to': self.date_to,
                    'past_due': past_due,
                    'subject': "Customer Statement [PAST DUE] - %s" % email_customer.name if past_due else "Customer Statement - %s" % email_customer.name
                }
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form_id.id, 'form')],
                    'view_id': compose_form_id.id,
                    'target': 'new',
                    'context': ctx,
                }
            t = threading.Thread(target=self.mail_loop, args=([invoices, email_customer, self.date_from, self.date_to, self.env.uid]))
            t.setName('CustomerStatement Email (Beta)')
            t.start()
        if pdf_customer:
            report = self.env.ref('customer_statement_report.report_customer_statement_pdf')
            return report.report_action(pdf_customer, data={
                'date_range': {
                    'd_from': self.date_from,
                    'd_to': self.date_to}
            })
