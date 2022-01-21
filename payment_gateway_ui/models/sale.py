# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.api import Environment
import odoo, time
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_is_zero
from datetime import datetime, timedelta, date
import logging


class SaleOrder(models.Model):
    _inherit = "sale.order"

    transaction_id = fields.Char('Transaction ID', copy=False)
    payment_id = fields.Char('Payment Profile ID', copy=False)
    transaction_date = fields.Datetime('Transaction Date', copy=False)
    refund = fields.Boolean('Refunded', copy=False)
    down_payment_amount = fields.Float(default=0.0, copy=False)
    gateway_type = fields.Selection([], string='Payment Gateway')

    def resend_link(self):
        """
        resend the link if expired
        """
        for record in self:
            pass #TODO remove me
