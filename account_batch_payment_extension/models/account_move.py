# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # todo not used anywhere
    # st_date = fields.Date(related='statement_line_id.date', readonly=True, store=True, string='Statement Date')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
