# -*- coding: utf-8 -*-
from odoo import fields, models, api, registry, SUPERUSER_ID, _
from odoo.exceptions import UserError

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
        if self._context.get('active_model', False) == 'res.partner' and self._context.get('active_ids', False):
            result['partner_ids'] = self.env['res.partner'].browse(self._context.get('active_ids'))
        return result

    def action_generate_statement(self):
        """
        process customer against with there invoices, payment with in a range of date.
        """
        inv_domain = [
            ('move_type', 'in', ['out_invoice', 'in_refund']),
            # ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', 'not in', ['draft', 'cancel'])
        ]

        payment_domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '!=', 'cancel')
        ]

        if self._context.get('active_model', False) == 'res.partner':
            inv_domain.append(('partner_id', 'in', self.partner_ids.ids))
            payment_domain.append(('partner_id', 'in', self.partner_ids.ids))

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

        for customer in email_customer:
            name = 'Customer statement: '+ customer.name
            customer.with_delay(description=name, channel='root.customerstatement').job_queue_mail_customer_statement(self.date_from, self.date_to, self.env.uid)
        if pdf_customer:
            report = self.env.ref('customer_statement_report.report_customer_statement_pdf')
            return report.report_action(pdf_customer, data={
                'date_range': {
                    'd_from': self.date_from,
                    'd_to': self.date_to}
            })
