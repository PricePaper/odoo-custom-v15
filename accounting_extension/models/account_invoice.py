# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    discount_date = fields.Date('Discount Till')

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        if self.payment_term_id and self.payment_term_id.is_discount:
            invoice_date = self.date_invoice
            self.discount_date = invoice_date + relativedelta(days=self.payment_term_id.due_days)
        return res

    @api.multi
    def action_cancel_draft(self):
        self.ensure_one()
        res = super(AccountInvoice, self).action_cancel_draft()
        vals = {'discount_date': False}
        if self.move_name:
            vals.update({'number': self.move_name})
        self.write(vals)
        return res

    def action_invoice_draft(self):
        self.ensure_one()
        res = super(AccountInvoice, self).action_invoice_draft()
        if self.move_name:
            self.write({'number': self.move_name})
        return res

    @api.multi
    def action_cancel_old(self):
        res = super(AccountInvoice, self).action_cancel()
        self.write({'move_name': False})
        return res