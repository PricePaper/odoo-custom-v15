# -*- coding: utf-8 -*-
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
            ('state', 'in', ['open', 'in_payment', 'paid'])
        ])
        default_account = self.env['ir.property'].get('property_account_receivable_id', 'res.partner')

        credit_lines = self.env['account.move.line'].search_read([
            ('partner_id', 'in', invoice_ids.mapped('partner_id').ids),
            ('account_id', '=', default_account.id),
            ('reconciled', '=', False),
            ('date', '>=', d_from),
            ('date', '<=', d_to),
            ('move_id.state', '=', 'posted'),
            '|',
            '&', ('amount_residual_currency', '!=', 0.0), ('currency_id', '!=', None),
            '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id', '=', None),
            ('amount_residual', '!=', 0.0),
            ('credit', '>', 0),
            ('debit', '=', 0)],
            ['partner_id', 'payment_id', 'ref', 'credit', 'date'])
        datas = {}
        for key, inv in groupby(invoice_ids.sorted(key=lambda r: r.partner_id.id), key=lambda i: (i.partner_id, i.has_outstanding)):
            inv = list(inv)
            if key[1]:
                if 'out_standing_credit' not in datas.get(str(key[0].id), {}):
                    datas.setdefault(str(key[0].id), {}).\
                        setdefault('out_standing_credit', []).\
                        extend([{
                        'ref': "%s (%s)" % (i['ref'], i['payment_id'] and i['payment_id'][1]) if i['ref'] else i['payment_id'] and i['payment_id'][1],
                        'date': i['date'],
                        'credit': i['credit']
                    } for i in filter(lambda r: r['partner_id'] and r['partner_id'][0] == key[0].id, credit_lines)])
                    datas[str(key[0].id)]['total_credit'] = sum(list(map(lambda r: r['credit'], datas[str(key[0].id)]['out_standing_credit'])))
            datas.setdefault(str(key[0].id), {}).\
                setdefault('open_invoices', []).\
                extend([{
                'ref': i.number,
                'amount_total': i.amount_total,
                'invoice_date': i.date_invoice,
                'due_date': i.date_due,
                'residual': i.residual
            } for i in inv if i.state == 'open'])
            datas[str(key[0].id)]['total'] = sum(list(map(lambda r: r['residual'], datas[str(key[0].id)]['open_invoices'])))
            datas.setdefault(str(key[0].id), {}). \
                setdefault('paid_invoices', []). \
                extend([{
                'ref': i.number,
                'amount_paid': p_move.credit,
                'invoice_date': p_move.date,
                'state': 'Posted',
                'balance': i.residual,
                'type': p_move.payment_id.payment_method_id.display_name
            } for i in inv for p_move in i.payment_move_line_ids])
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

