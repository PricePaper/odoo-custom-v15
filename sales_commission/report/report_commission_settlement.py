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

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.commission.settlement'].browse(docids)
        return {'doc_ids': docs.ids,
                'doc_model': 'sale.commission.settlement',
                'docs': docs,
                'data': data,
            }





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
