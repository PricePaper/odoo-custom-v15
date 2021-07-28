# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar


class Reportcommission_audit(models.AbstractModel):

    _name = "report.sales_commission.report_commission_audit"
    _description = 'Commission Audit report'

    def get_commission_lines(self, docs):
        commission_vals={}
        for doc in docs:
            month = doc.month.split('-')[0]
            year = doc.month.split('-')[1]

            month_last_date = calendar.monthrange(int(year), int(month))[1]
            from_date = "%s%s01"%(year, month)
            from_date = datetime.strptime(from_date, "%Y%m%d").date()
            to_date = "%s%s%s" %(year, month, month_last_date)
            to_date = datetime.strptime(to_date, "%Y%m%d").date()
            invoices = self.env['account.invoice'].search([('state', '=', 'paid'), ('type', 'in', ('out_invoice', 'out_refund'))])
            invoices = invoices.filtered(lambda r: r.paid_date and r.paid_date >= from_date and r.paid_date <= to_date)
            for invoice in invoices:
                if invoice.paid_date and invoice.paid_date >= from_date and invoice.paid_date <= to_date:
                    for rec in invoice.partner_id.commission_percentage_ids:
                        if not rec.rule_id:
                            continue
                        commission = 0
                        profit = invoice.gross_profit
                        if rec.rule_id.based_on in ['profit', 'profit_delivery']:
                            if invoice.payment_term_id.due_days:
                                days = invoice.payment_term_id.due_days
                                if invoice.paid_date and invoice.paid_date > invoice.date_invoice + relativedelta(days=days):
                                    profit += invoice.amount_total * (invoice.payment_term_id.discount_per / 100)
                            payment = invoice.payment_ids.filtered(lambda r: r.payment_method_id.code == 'credit_card')
                            if payment and invoice.partner_id.payment_method != 'credit_card':
                                profit -= invoice.amount_total * 0.03
                            if not payment and invoice.partner_id.payment_method == 'credit_card':
                                profit += invoice.amount_total * 0.03
                            if profit <= 0:
                                continue
                            commission = profit * (rec.rule_id.percentage / 100)
                        elif rec.rule_id.based_on == 'invoice':
                            amount = invoice.amount_total
                            commission = amount * (rec.rule_id.percentage / 100)
                        if commission == 0:
                            continue
                        type = 'Invoice'
                        if invoice.type == 'out_refund':
                            commission = -commission
                            type = 'Refund'

                        sale = invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                        vals = {
                            'sale_person_id': rec.sale_person_id,
                            'sale_id': sale and sale,
                            'commission': commission,
                            'invoice_id': invoice,
                            'invoice_type': type,
                            'is_paid': True,
                            'invoice_amount': invoice.amount_total,
                            'commission_date': invoice.date_invoice and invoice.paid_date
                        }



                        if commission_vals.get(rec.sale_person_id):
                            if commission_vals.get(rec.sale_person_id).get(invoice.partner_id):
                                if commission_vals.get(rec.sale_person_id).get(invoice.partner_id).get(invoice):
                                    commission_vals[rec.sale_person_id][invoice.partner_id][invoice].append(vals)
                                else:
                                    commission_vals[rec.sale_person_id][invoice.partner_id][invoice] = [vals]
                            else:
                                commission_vals[rec.sale_person_id][invoice.partner_id] = {invoice : [vals]}
                        else:
                            commission_vals[rec.sale_person_id] = {invoice.partner_id: {invoice : [vals]}}

                        if invoice.paid_date > invoice.date_due:
                            extra_days = invoice.paid_date - invoice.date_due
                            if invoice.partner_id.company_id.commission_ageing_ids:
                                commission_ageing = invoice.partner_id.company_id.commission_ageing_ids.filtered(
                                    lambda r: r.delay_days <= extra_days.days)
                                commission_ageing = commission_ageing.sorted(key=lambda r: r.delay_days, reverse=True)
                                if commission_ageing and commission_ageing[0].reduce_percentage:
                                    commission = commission_ageing[0].reduce_percentage * commission / 100
                                    vals = {
                                        'sale_person_id': rec.sale_person_id,
                                        'sale_id': sale,
                                        'commission': -commission,
                                        'invoice_id': invoice,
                                        'invoice_type': 'Commission Aging',
                                        'is_paid': True,
                                        'invoice_amount': invoice.amount_total,
                                        'commission_date': invoice.paid_date
                                    }
                                    if commission_vals.get(rec.sale_person_id):
                                        if commission_vals.get(rec.sale_person_id).get(invoice.partner_id):
                                            if commission_vals.get(rec.sale_person_id).get(invoice.partner_id).get(invoice):
                                                commission_vals[rec.sale_person_id][invoice.partner_id][invoice].append(vals)
                                            else:
                                                commission_vals[rec.sale_person_id][invoice.partner_id][invoice] = [vals]
                                        else:
                                            commission_vals[rec.sale_person_id][invoice.partner_id] = {invoice : [vals]}
                                    else:
                                        commission_vals[rec.sale_person_id] = {invoice.partner_id: {invoice : [vals]}}
        return commission_vals


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['generate.sales.commission'].browse(docids)
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking.batch',
                'docs': docs,
                'data': data,
                'get_commission_lines': self.get_commission_lines,
            }





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
