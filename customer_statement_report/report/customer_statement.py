# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import models, api
from itertools import groupby

class CustomerStatementPdfReport(models.AbstractModel):

    _name = "report.customer_statement_report.customer_statement_pdf"
    _description = 'Customer Statement (Pdf)'

    def _get_partner_ledger_info(self, partner, date_from, date_to):
        ledger_OBJ = self.env['account.partner.ledger']
        options = {
            'unposted_in_period': True,
            'unfolded_lines': [],
            'unreconciled': True,
            'cash_basis': False,
            'all_entries': False,
            'analytic': None,
            'account_type': [
                {'selected': False, 'id': 'receivable', 'name': 'Receivable'},
                {'selected': False, 'id': 'payable', 'name': 'Payable'}],
            'partner_ids': partner.ids,
            'partner': True,
            'date': {
                'date_to': date_to,
                'date_from': date_from,
                'filter': 'custom'
            }
        }
        context = dict(self._context)
        context.update({
            'date_to': date_to,
            'date_from': date_from,
            'model': 'account.partner.ledger',
            'company_ids': self.env.user.company_id.ids,
            'state': 'posted',
            'strict_range': True
        })
        info = ledger_OBJ.with_context(**context)._get_lines(options)

        today = date.today()
        due_flag = False
        for line in info:
            if 'colspan' not in line:
                if today > line['columns'][3]['name']:
                    due_flag = True
                    break

        payments = self.env['account.payment'].search([
            ('partner_id', '=', partner.id),
            ('payment_date', '>=', date_from),
            ('payment_date', '<=', date_to),
            ('state', '!=', 'cancelled'),
            ('invoice_ids', '!=', False)
        ])
        payment_list = []
        for payment in payments:
            payment_list.append({
                'p_name': payment.name,
                'payment_date': payment.payment_date,
                'amount_paid': payment.amount,
                'type': payment.payment_method_id.display_name,
                'state': 'Posted',
                'balance': sum(payment.invoice_ids.mapped('payment_move_line_ids').filtered(lambda p: p.payment_id).mapped('amount_residual')),
                'ref': ','.join(payment.invoice_ids.mapped('number'))
            })
        return {
            'open_credits': info,
            'payments': payment_list,
            'past_due': due_flag
        }

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

        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': partner,
            'data': data,
            'company_id': self.env.user.company_id,
            'd_from': d_from,
            'd_to':  d_to,
            'get_data': self._get_partner_ledger_info
            }

