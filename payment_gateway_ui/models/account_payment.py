# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    transaction_id = fields.Char(string='Transaction ID', copy=False)
    transaction_partner_id = fields.Many2one('res.partner', string='Authorized Customer', copy=False)
    payment_id = fields.Char(string='Payment ID', copy=False)
    extra_content = fields.Text('Customer Notes', copy=False)



class AccountMove(models.Model):
    _inherit = "account.move"

    message = fields.Text('Note')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
