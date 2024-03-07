# -*- encoding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"


    @api.model
    def _cron_purge_old_open_credits(self):
        """
        Cron method to identify old open credit notes and writeoff the amount
        """
        limit_days = self.env.user.company_id and self.env.user.company_id.purge_old_open_credit_limit or 120
        domain_date = datetime.today() - timedelta(days=limit_days)
        credit_notes = self.search([
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_refund'),
            ('payment_state','in',('not_paid','in_payment','partial')),
            ('invoice_date', '<', domain_date.strftime('%Y-%m-%d')),
        ]).sudo()

        payment_limit_days = self.env['ir.config_parameter'].sudo().get_param('purge_old_open_credits.purge_old_payment_day_limit')
        pay_domain_date = datetime.today() - timedelta(days=int(payment_limit_days))
        accounts = self.env['account.account'].search([]).filtered(lambda r: r.user_type_id.type in ('receivable', 'payable'))


        domain = [
            ('date', '<', pay_domain_date.strftime('%Y-%m-%d')),
            ('account_id', 'in', accounts.ids),
            ('parent_state', '=', 'posted'),
            ('reconciled', '=', False),
            '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0), ('balance', '<', 0.0)
        ]
        move_lines = self.env['account.move.line'].search(domain)
        # payment = move_lines.move_id.filtered(lambda r: r.move_type == 'entry' and r.payment_id != False and r.payment_id.payment_type == 'inbound')
        for line in move_lines:
            if line.move_id.move_type == 'entry' and line.move_id.payment_id != False and line.move_id.payment_id.payment_type == 'inbound':
                print(line.move_id.name, line.amount_residual)
                line.move_id.create_purge_writeoff(line.amount_residual)
                break


        for invoice in credit_notes:
            invoice.create_purge_writeoff()
        # for payment in payments:
        #     payment.create_purge_writeoff()
        return True

    def create_purge_writeoff(self, wrt_amt=0):
        """
        Writeoff the balance amount and reconcile the credit note
        """
        self.ensure_one()
        rev_line_account = self.partner_id and self.partner_id.property_account_receivable_id
        if not rev_line_account:
            rev_line_account = self.env['ir.property'].\
                with_context(force_company=self.company_id.id).get('property_account_receivable_id', 'res.partner')

        if self.move_type == 'out_refund':
            wrtf_account = self.env['ir.config_parameter'].sudo().get_param('purge_old_open_credits.credit_purge_account')
            label = 'Old Credit Purge'
        else:
            wrtf_account = self.env['ir.config_parameter'].sudo().get_param('purge_old_open_credits.payment_purge_account')
            label = 'Old Payment Purge'
        company_currency = self.company_id.currency_id

        if not wrtf_account:
            raise UserError(_('Please set a Write off account for credit Purge.'))


        wrtf_amount = self.amount_residual
        if wrt_amt:
            wrtf_amount = abs(wrt_amt)
        amobj = self.env['account.move'].create({
            'company_id': self.company_id.id,
            'date': fields.Date.today(),
            'journal_id': self.journal_id.id,
            'ref': self.payment_reference,
            'line_ids': [(0, 0, {
                'account_id': rev_line_account.id,
                'company_currency_id': company_currency.id,
                'debit': wrtf_amount,
                'credit': 0,
                'journal_id': self.journal_id.id,
                'name': label,
                'partner_id': self.partner_id.id
            }), (0, 0, {
                'account_id': int(wrtf_account),
                'company_currency_id': company_currency.id,
                'debit': 0,
                'credit': wrtf_amount,
                'journal_id': self.journal_id.id,
                'name': label,
                'partner_id': self.partner_id.id
             })]
        })
        amobj.action_post()
        rcv_lines = self.line_ids.filtered(lambda r: r.account_id.user_type_id.type == 'receivable')
        rcv_wrtf = amobj.line_ids.filtered(lambda r: r.account_id.user_type_id.type == 'receivable')
        (rcv_lines + rcv_wrtf).reconcile()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
