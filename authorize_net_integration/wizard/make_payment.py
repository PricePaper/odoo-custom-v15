# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError


class make_payment(models.TransientModel):
    _inherit = "make.payment"
    _description = "Make Payment Class"

    @api.model
    def _get_payment_ids(self):
        if not self.env.context.get('active_id'):
            return []
        partner_brw = self.env['res.partner'].browse(self.env.context.get('default_partner_id', 0))
        profile_id = partner_brw and partner_brw._get_profile_id() or False
        if not profile_id:
            return []
        res = self.env['authorizenet.api']._get_profile(profile_id)
        return self.env['authorizenet.api']._get_payment_ids(res)

    @api.model
    def _payment_count(self):
        partner_brw = self.env['res.partner'].browse(self.env.context.get('default_partner_id', 0))
        profile_id = partner_brw and partner_brw._get_profile_id() or False
        if not profile_id:
            return 0
        res = self.env['authorizenet.api']._get_profile(profile_id)
        return len(self.env['authorizenet.api']._get_payment_ids(res))

    # Same for both Sale order and Invoice
    @api.one
    def authorize_transaction(self):
        """
        create authorizenet payment and  authorize transaction
        """
        authorize_obj = self.env['authorizenet.api']
        active_brw = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id', []))
        invoice = ''
        sale_obj = ''
        if self.env.context.get('active_model', '') == 'sale.order':
            sale_obj = active_brw
            print('sale_obj', sale_obj)
            journal_rec = self.env['account.journal'].sudo().search([('is_authorizenet', '=', True)], limit=1)
            surcharge_percentage = journal_rec and journal_rec.surcharge_user or 0
            handling_fee = (sale_obj.amount_total * surcharge_percentage) / 100
            total_amount = handling_fee + sale_obj.amount_total
            paid_amount = 0
            InvoiceRec = sale_obj.sudo().create_down_payment(total_amount, handling_fee, sale_obj.amount_total,
                                                             paid_amount)
            print('InvoiceRec', InvoiceRec)
        elif self.env.context.get('active_model', '') == 'account.invoice':
            invoice = active_brw.origin
            InvoiceRec = active_brw
            # sale_obj = self.env['sale.order'].search([('name', '=', invoice)])
        profile_id = self.partner_id._get_profile_id()
        if self.is_correction:
            try:
                authorize_obj.void_payment(profile_id, active_brw.payment_id, active_brw.transaction_id)
            except:
                pass
        expairy_date = '%s-%s' % (self.exp_year, self.exp_month)
        if not profile_id:
            profile_id = authorize_obj.create_authorizenet_profile(self.partner_id)
            self.commit_cursor(self.partner_id and self.partner_id, profile_id)
        payment_id = self.payment_id
        if not payment_id:
            payment_id = authorize_obj.create_payment_profile(profile_id, self.partner_id, self.card_no, self.card_code,
                                                              expairy_date)

        journal_rec = self.env['account.journal'].sudo().search([('is_authorizenet', '=', True)], limit=1)
        surcharge_percentage = journal_rec and journal_rec.surcharge_user or 0
        handling_fee = (InvoiceRec.residual * surcharge_percentage) / 100
        amount = InvoiceRec.residual + handling_fee
        payment = InvoiceRec.with_context({'payment_amount': amount}).register_card_payments()
        transaction_id = authorize_obj.authorize_payment(profile_id, payment_id, InvoiceRec.residual, InvoiceRec.number)
        payment.write(
            {'transaction_id': transaction_id, 'payment_id': payment_id})
        self.env['authorizenet.api'].capture_payment(profile_id, payment_id, transaction_id, InvoiceRec.residual)
        InvoiceRec.write(
            {'transaction_id': transaction_id, 'payment_id': payment_id,
             'due_amount_gateway': InvoiceRec.due_amount_gateway + InvoiceRec.residual,
             'transaction_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        if sale_obj:
            sale_obj.write(
                {'transaction_id': transaction_id,
                 'payment_id': payment_id,
                 'transaction_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

        if self.env.context.get('active_model', '') == 'sale.order':
            Template = self.env.ref('payment_gateway_ui.email_template_payment_notifications_inside_sales')
            if Template:
                Template.send_mail(sale_obj.id, force_send=False)
        else:
            Template = self.env.ref('payment_gateway_ui.email_template_payment_notifications_inside_invoice')
            if Template:
                Template.send_mail(InvoiceRec.id, force_send=False)
        payment.post()
        default_account = self.env['ir.property'].get('property_account_receivable_id', 'res.partner')
        move_vals = payment._get_move_vals()
        move_vals.update({'line_ids': [[0, 0, {
            'partner_id': payment.payment_type in ('inbound', 'outbound') and self.env[
                'res.partner']._find_accounting_partner(payment.partner_id).id or False,
            'debit': 0,
            'credit': float(handling_fee),
            # 'amount_currency': amount_currency or False,
            'account_id': payment.journal_id.surcharge_account_id.id,
            'currency_id': payment.journal_id.currency_id.id,
            'journal_id': payment.journal_id.id
        }], [0, 0, {
            'partner_id': payment.payment_type in ('inbound', 'outbound') and self.env[
                'res.partner']._find_accounting_partner(payment.partner_id).id or False,
            'debit': float(handling_fee),
            'credit': 0,
            # 'amount_currency': amount_currency or False,
            'account_id': default_account.id,
            'currency_id': payment.journal_id.currency_id.id,
            'journal_id': payment.journal_id.id
        }]]})
        move = self.env['account.move'].create(move_vals)
        move.post()
        (move.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in (
            'payable', 'receivable')) + payment.move_line_ids.filtered(
            lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))).reconcile()
        return self.write({'card_no': '', 'card_code': ''})

    def commit_cursor(self, partner_id, profile_id=False, context=None):
        """
        except raise would hinder commiting data
        (writing profile id to partner)
        couldnt get new api to create and commit
        data using new cursor
        so executing the old fashioned way
        """
        if partner_id and profile_id:
            partner_id.write({'profile_id': profile_id})
            self.env.cr.commit()
        return True

    payment_nos = fields.Integer('Payment Numbers', default=_payment_count)
    payment_id = fields.Selection(_get_payment_ids, 'Your last Card')


make_payment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
