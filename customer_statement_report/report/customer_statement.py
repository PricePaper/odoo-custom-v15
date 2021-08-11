# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import models, api
from itertools import groupby

class CustomerStatementPdfReport(models.AbstractModel):

    _name = "report.customer_statement_report.customer_statement_pdf"
    _description = 'Customer Statement (Pdf)'

    @api.model
    def _get_report_values(self, docids, data=None):
        partner = self.env['res.partner'].browse(docids)
        if not partner:
            docids = data.get('context', {}).get('active_ids')
            partner = self.env['res.partner'].browse(docids)
        if data.get('date_range', False):
            d_from = data['date_range']['d_from']
            d_to = data['date_range']['d_to']
        else:
            d_from = self._context.get('d_from')
            d_to = self._context.get('d_to')
        invoice_ids = self.env['account.invoice'].search([
            ('partner_id', 'in', partner.ids),
            ('type', 'in', ['out_invoice', 'in_refund']),
            ('date_invoice', '>=', d_from),
            ('date_invoice', '<=', d_to),
            ('state', 'not in', ['cancel'])
        ])
        invoices_open_with_credit = invoice_ids.filtered(lambda r: r.has_outstanding and r.state in ['open', 'in_payment'])
        invoices_paid = invoice_ids.filtered(lambda r: r.state == 'paid')
        invoice_ids = invoices_open_with_credit | invoices_paid
        default_account = self.env['ir.property'].get('property_account_receivable_id', 'res.partner')
        credit_lines = self.env['account.move.line'].search_read([
            ('partner_id', 'in', invoice_ids.mapped('partner_id').ids),
            ('account_id', '=', default_account.id),
            ('reconciled', '=', False),
            ('move_id.state', '=', 'posted'),
            '|',
            '&', ('amount_residual_currency', '!=', 0.0), ('currency_id', '!=', None),
            '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id', '=', None),
            ('amount_residual', '!=', 0.0),
            ('credit', '>', 0),
            ('debit', '=', 0)],
            ['partner_id', 'payment_id', 'ref', 'credit', 'date', 'name', 'amount_residual'])
        datas = {}
        for key, inv in groupby(invoice_ids.sorted(key=lambda r: r.partner_id.id), key=lambda i: i.partner_id):
            inv = list(inv)
            if 'out_standing_credit' not in datas.get(str(key.id), {}):
                datas.setdefault(str(key.id), {}).\
                    setdefault('out_standing_credit', []).\
                    extend([{
                    'ref':  i['payment_id'] and i['payment_id'][1] or '',
                    'date': i['date'],
                    'credit': -i['credit'],
                    'balance': i['amount_residual']
                } for i in filter(lambda r: r['partner_id'] and r['partner_id'][0] == key.id, credit_lines)])
                datas[str(key.id)]['total_credit'] = sum(list(map(lambda r: r['credit'], datas[str(key.id)]['out_standing_credit'])))
            datas.setdefault(str(key.id), {}).\
                setdefault('open_invoices', []).\
                extend([{
                'ref': i.number,
                'amount_total': i.amount_total,
                'invoice_date': i.date_invoice,
                'due_date': i.date_due,
                'residual': i.residual
            } for i in inv if i.state == 'open'])
            datas[str(key[0].id)]['total'] = sum(list(map(lambda r: r['residual'], datas[str(key.id)]['open_invoices'])))
            payments = self.env['account.payment']
            for rec in inv:
                for p_move in rec.payment_move_line_ids:
                    payments |= p_move.payment_id
            datas.setdefault(str(key.id), {}). \
                setdefault('paid_invoices', []). \
                extend([{
                'ref': ','.join(payment.invoice_ids.mapped('number')),
                'amount_paid': payment.amount,
                'p_name': payment.name,
                'payment_date': payment.payment_date,
                'state': 'Posted',
                'balance': sum(payment.invoice_ids.mapped('payment_move_line_ids').filtered(lambda p: p.payment_id).mapped('amount_residual')),
                'type': payment.payment_method_id.display_name
            } for payment in payments])
            past_due = False
            for rec in inv:
                if rec.state == 'open':
                    term_line = rec.payment_term_id.line_ids.filtered(lambda r: r.value == 'balance')
                    date_due = rec.date_due
                    if term_line and term_line.grace_period:
                        date_due = rec.date_due + timedelta(days=term_line.grace_period)
                    if date_due < date.today():
                        past_due = True
                        break
            datas[str(key[0].id)]['past_due'] = past_due
        else:
            data.update(datas)
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': partner,
            'data': data,
            'company_id': self.env.user.company_id,
            'credit_lines': credit_lines,
            'report_date': '%s / %s' % (d_from, d_to)
            }

