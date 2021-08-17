# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.tools import float_round
import math


class Reportcommission_audit(models.AbstractModel):

    _name = "report.sales_commission.report_commission_settlement"
    _description = 'Commission Settlement report'

    def get_commission_lines(self, doc):
        commission_vals={}
        for commission in doc.commission_ids:
            if not commission.invoice_id:
                if commission_vals.get(False):
                    commission_vals[False].append(commission)
                else:
                    commission_vals[False] = [commission]
                continue

            if commission_vals.get(commission.invoice_id.partner_id):
                commission_vals[commission.invoice_id.partner_id].append(commission)
            else:
                commission_vals[commission.invoice_id.partner_id] = [commission]
        return commission_vals


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.commission.settlement'].browse(docids)
        return {'doc_ids': docs.ids,
                'doc_model': 'sale.commission.settlement',
                'docs': docs,
                'data': data,
                'get_commission_lines': self.get_commission_lines,
            }





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
