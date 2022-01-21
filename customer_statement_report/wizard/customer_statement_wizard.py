# -*- coding: utf-8 -*-
from odoo import fields, models, api, registry,SUPERUSER_ID, _
from odoo.exceptions import UserError
import threading
import logging

_logger = logging.getLogger(__name__)

class CustomerStatementWizard(models.TransientModel):
    _name = 'customer.statement.wizard'
    _description = 'Customer Statement Generator'

    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    partner_ids = fields.Many2many('res.partner', string="Recipients")

    @api.model
    def default_get(self, fields):
        result = super(CustomerStatementWizard, self).default_get(fields)
        result['date_from'] = self.env.user.company_id.last_statement_date
        return result



    def action_generate_statement(self):
        """
        process customer against with there invoices, payment with in a range of date.
        """
        pass #TODO remove me
