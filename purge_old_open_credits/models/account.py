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
        for invoice in credit_notes:
            invoice.create_purge_writeoff()
        return True

    def create_purge_writeoff(self):
        """
        Writeoff the balance amount and reconcile the credit note
        """
        self.ensure_one()
        rev_line_account = self.partner_id and self.partner_id.property_account_receivable_id
        if not rev_line_account:
            rev_line_account = self.env['ir.property'].\
                with_context(force_company=self.company_id.id).get('property_account_receivable_id', 'res.partner')

        wrtf_account = self.env['ir.config_parameter'].sudo().get_param('purge_old_open_credits.credit_purge_account')
        company_currency = self.company_id.currency_id

        if not wrtf_account:
            raise UserError(_('Please set a Write off account for credit Purge.'))

        wrtf_amount = self.amount_residual

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
                'name': 'Old Credit Purge',
                'partner_id': self.partner_id.id
            }), (0, 0, {
                'account_id': int(wrtf_account),
                'company_currency_id': company_currency.id,
                'debit': 0,
                'credit': wrtf_amount,
                'journal_id': self.journal_id.id,
                'name': 'Old Credit Purge',
                'partner_id': self.partner_id.id
             })]
        })
        amobj.action_post()
        rcv_lines = self.line_ids.filtered(lambda r: r.account_id.user_type_id.type == 'receivable')
        rcv_wrtf = amobj.line_ids.filtered(lambda r: r.account_id.user_type_id.type == 'receivable')
        (rcv_lines + rcv_wrtf).reconcile()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
