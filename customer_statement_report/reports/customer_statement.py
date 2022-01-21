# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import models, api
from odoo.tools.float_utils import float_round

class CustomerStatementPdfReport(models.AbstractModel):

    _name = "report.customer_statement_report.customer_statement_pdf"
    _description = 'Customer Statement (Pdf)'


