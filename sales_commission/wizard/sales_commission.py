# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar


class GenerateCommission(models.TransientModel):
    _name = 'generate.sales.commission'
    _description = 'Generate Sales commission'

    @api.model
    def _get_months(self):
        res = []
        startdate = datetime.now()
        for i in range(0,12):
            date = startdate - relativedelta(months=i)
            key = format(date, '%m-%Y')
            value = format(date, '%B %Y')
            res.append((key, value))
        return res

    month = fields.Selection(string="Month", selection=_get_months, required=True)

    @api.multi
    def generate_commission(self):
        return self.env.ref('sales_commission.commission_audit_report').report_action(self)



GenerateCommission()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
