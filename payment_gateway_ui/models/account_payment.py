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

    @api.model
    def default_get(self, fields):
        """updates the super method prepared dict of values with additional three fields
            triggered by pressing register payment button in invoice form"""

        res = super(AccountPayment, self).default_get(fields)
        invoice = self.env['account.invoice'].browse(self._context.get('active_id'))
        if invoice.transaction_id:
            res.update({'transaction_partner_id': invoice.partner_id.id, 'transaction_id': invoice.transaction_id,
                        'payment_id': invoice.payment_id or None})
        return res


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.register.payments"

    def create_payments(self):
        context = dict(self._context)
        if all(invoice.type == 'out_refund' for invoice in self.invoice_ids):
            for invoice in self.invoice_ids:
                invoice.write({'is_refund': True})
                invoice.invoice_origin_id and invoice.invoice_origin_id.write({'is_refund': True})
        else:
            context.update({'refund_mode': True})
        res = super(AccountRegisterPayment, self.with_context(context)).create_payments()
        return res


AccountRegisterPayment()


class AccountMove(models.Model):
    _inherit = "account.move"

    message = fields.Text('Note')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
