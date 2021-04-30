# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
import time


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    is_refund = fields.Boolean('Is Refunded', default=False, copy=False)
    transaction_id_refund = fields.Char("Refunded transaction ID", copy=False)
    invoice_origin_id = fields.Many2one('account.invoice', "Invoice Origin ID", copy=False)
    refund_invoice_ids = fields.One2many('account.invoice', 'invoice_origin_id', string="Refunded Ids")
    due_amount_gateway = fields.Float('Due', copy=False)
    transaction_id = fields.Char('Transaction ID', copy=False)
    payment_id = fields.Char('Payment Profile ID', copy=False)
    transaction_date = fields.Datetime('Transaction Date', copy=False)
    sale_ids = fields.Many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Invoices',
                                readonly=True)
    parent_invoice_id = fields.Many2one('account.invoice', 'Reference Invoice', copy=False)
    correction_reason = fields.Text('Reason for Correction', copy=False)
    gateway_type = fields.Selection([], string='Payment Gateway')

    @api.multi
    def resend_link(self):
        """
        resend the link if expired
        """
        for record in self:
            gateway_type = self.env['ir.config_parameter'].sudo().get_param('gateway_type')
            if not gateway_type:
                raise UserError(_('Warning ! \n Please check Payment Gateway configuration.'))
            Journal = self.env['account.journal'].search([('is_authorizenet', '=', True)], limit=1)
            if not Journal:
                raise UserError(_(
                'Error! \n Please Select The Authorize.net Journal.(Accounting->configuration->journal->Authorize.net Journal->True!'))
            if record.state == 'open':
                self.env['payment.token.invoice'].edi_token_recreate(record, 'invoice')
                template_id = self.env.ref('payment_gateway_ui.email_invoice_online_link')
                if not template_id:
                    raise UserError(_('Warning ! \n No Email Template found.'))
                compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
                ctx = dict(
                    default_model='account.invoice',
                    default_res_id=self.id,
                    default_use_template=bool(template_id),
                    default_template_id=template_id.id,
                    default_composition_mode='comment',
                    mark_invoice_as_sent=True,
                )
                return {
                    'name': _('Compose Email'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form.id, 'form')],
                    'view_id': compose_form.id,
                    'target': 'new',
                    'context': ctx,
                }

        return

    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        res = super(AccountInvoice, self).assign_outstanding_credit(credit_aml_id)
        self.ensure_one()
        payment_records = self.env['payment.token.invoice'].search(
            [('invoice_id', '=', self.id), ('model', '=', 'invoice')])
        for rec in payment_records:
            if rec.invoice_id.state != 'open':
                rec.state = 'expired'
        for rec in self.filtered(lambda inv: inv.type == 'out_refund'):
            if rec.transaction_id:
                rec.write({'is_refund': True})
                if rec.invoice_origin_id:
                    rec.invoice_origin_id.write({'is_refund': True})
        return res

    def get_invoice_payment_url(self):
        """
        return the payment url
        :return:
        """
        token = self.env['payment.token.invoice'].get_invoice_payment_record(self, 'invoice')
        web_root_url = self.env['ir.config_parameter'].get_param('web.base.url')
        gateway_type = self.env['ir.config_parameter'].sudo().get_param('gateway_type')
        print('gateway_type', gateway_type)
        EDI_VIEW_WEB_URL = '%s/%s/payment/invoice?token=%s' % (web_root_url, gateway_type, token)

        return EDI_VIEW_WEB_URL

    @api.multi
    def action_reopen(self):
        for invoice in self:
            if invoice.is_refund and invoice.transaction_id_refund:
                continue
            else:
                super(AccountInvoice, invoice).action_reopen()
        return True

    @api.multi
    def write(self, vals):
        if vals.get('payment_id', False):
            for row in self:
                row.partner_id and row.partner_id.write({'payment_id': vals.get('payment_id', False)})
        return super(AccountInvoice, self).write(vals)

    @api.model
    def create(self, vals):
        id = super(AccountInvoice, self).create(vals)
        if vals.get('payment_id', False):
            self.partner_id and self.partner_id.write({'payment_id': vals.get('payment_id', False)})
        return id


AccountInvoice()
