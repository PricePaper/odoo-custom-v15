# -*- coding: utf-8 -*-
from datetime import datetime,date, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, api,_
from odoo.tools.float_utils import float_round

class CustomerStatementPdfReport(models.AbstractModel):

    _name = "report.customer_statement_report.customer_statement_pdf"
    _description = 'Customer Statement (Pdf)'

    def _get_partner_ledger_info(self, partner, date_from, date_to):
        ledger_OBJ = self.env['account.partner.ledger']
        options = {
            'unposted_in_period': True,
            'unfolded_lines': ['partner_%s' % (partner if partner else 0) for partner in partner.ids],
            'allow_domestic' : False,
            'fiscal_position': 'all',
            'available_vat_fiscal_positions': [],
            'unreconciled': False,
            'all_entries': False,
            'account_type': [{'id': 'receivable', 'name': _('Receivable'), 'selected': False},
                             {'id': 'payable', 'name': _('Payable'), 'selected': False}],
            'partner_ids': partner.ids,
            'partner': True,
            'strict_range': True,
            'date': {
                'date_to': date_to,
                'date_from': date_from,
                'filter': 'custom',
                'mode': 'range',
            }
        }


        info = ledger_OBJ._get_lines(options)
        today = date.today()
        data = {'cumulative': 0, 'open_credits': [], 'payments': [], 'past_due': False}


        follow_up_OBJ = self.env['account.followup.report']
        follow_options = {'partner_id': partner.id, 'followup_level': (1, 15)}
        follow_up_info = follow_up_OBJ._get_lines(follow_options)
        amount = 0
        for line in follow_up_info:

            if line.get('account_move', False):
                if line['columns'][6]['name']:
                    continue

                aml_id = self.env['account.move.line'].browse(line['id'])
                if line['columns'][2]['name']:
                    if aml_id.move_id.is_inbound() and today > datetime.strptime(line['columns'][2]['name'], "%m/%d/%Y").date() and not aml_id.reconciled and not aml_id.payment_id:
                        data['past_due'] = True

                move = line.get('account_move', False)

                amount += aml_id.amount_residual
                amount_due = aml_id.amount_residual
                data['open_credits'].append(
                    {
                        'ref': line.get('name'),
                        'date': line['columns'][0]['name'],
                        'due_date': line['columns'][2]['name'],
                        'amount': aml_id.balance,
                        'amount_due': ('$ ', '-$ ')[amount_due < 0] + str(round(abs(amount_due), 2) or 0.00),
                        'running_balance': ('$ ', '-$ ')[amount < 0] + str(round(abs(amount), 2) or 0.00),
                    }
                )
        else:
            data['cumulative'] = ('$ ', '-$ ')[amount < 0] + str(round(abs(amount), 2) or 0.0)

        for line in info:
            if 'colspan' not in line:
                aml_id = self.env['account.move.line'].browse(line['id'])
                if not aml_id.reconciled and (aml_id.payment_id or line['caret_options'] == 'account.move'):
                    pass
                elif line['caret_options'] == 'account.payment':
                    payment = aml_id.payment_id
                    data['payments'].append(
                        {
                            'p_name': payment.name,
                            'payment_date': payment.date,
                            'amount_paid': payment.amount,
                            'type': payment.payment_method_id.display_name,
                            'state': 'Posted',
                            'balance': sum(payment.invoice_line_ids.filtered(lambda p: p.payment_id).mapped('amount_residual')),
                            'ref': ','.join(payment.invoice_line_ids.mapped('move_id.name'))
                        }
                    )

        return data

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
