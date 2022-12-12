# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.tools import float_round
import math


class ReportCommissionAudit(models.AbstractModel):
    _name = "report.sales_commission.report_commission_audit"
    _description = 'Commission Audit report'

    def get_commission_lines(self, docs):

        commission_vals = {}
        for doc in docs:
            commission_vals = doc.get_commission_vals()
        commission_diff = {}
        for rep, partners in commission_vals.items():
            for partner, invoices in partners.items():
                for invoice, vals_list in invoices.items():
                    commission = 0
                    for vals in vals_list:
                        commission += vals.get('commission')
                    old_commission_lines = invoice.mapped('sale_commission_ids').filtered(lambda r: r.sale_person_id == rep and r.is_paid)
                    old_commission = old_commission_lines and sum(old_commission_lines.mapped('commission')) or 0

                    if float_round(commission, precision_digits=2) != float_round(old_commission, precision_digits=2):
                        if math.isclose(commission, old_commission, abs_tol=0.1):
                            continue
                        vals1 = {'old_commission': float_round(old_commission, precision_digits=2),
                                 'commission_audit': float_round(commission, precision_digits=2)}
                        if commission_diff.get(rep):
                            if commission_diff.get(rep).get(partner):
                                if commission_diff.get(rep).get(partner).get(invoice):
                                    commission_diff[rep][partner][invoice].append(vals1)
                                else:
                                    commission_diff[rep][partner][invoice] = [vals1]
                            else:
                                commission_diff[rep][partner] = {invoice: [vals1]}
                        else:
                            commission_diff[rep] = {partner: {invoice: [vals1]}}
        return commission_diff

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
