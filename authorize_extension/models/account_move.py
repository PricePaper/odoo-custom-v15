# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_authorize_tx_failed = fields.Boolean('Authorize.net Transaction Failed')

    def action_register_payment(self):

        if self.mapped('authorized_transaction_ids').filtered(lambda r: r.state in ('authorized', 'done')):
            raise ValidationError(_("Selected Invoice(s) have/has authorized or confirmed transaction."))
        return super(AccountMove, self).action_register_payment() 


    def action_reautherize_transaction(self):
        self.ensure_one()

        if self.is_authorize_tx_failed:
            token = self.partner_id.get_authorize_token()
            error_msg = ''
            if not token:
                error_msg = "There is no authorise.net token available in %s" % self.partner_id.display_name
                self.write({'is_authorize_tx_failed': True})
            else:
                self.write({'is_authorize_tx_failed': False})
                reference = self.name
                count = self.env['payment.transaction'].sudo().search_count([('reference', 'ilike', self.name)])
                if count:
                    reference = '%s - %s' % (self.name, count)
                tx_sudo = self.env['payment.transaction'].sudo().create({
                    'acquirer_id': token.acquirer_id.id,
                    'reference': reference,
                    'amount': self.amount_total,
                    'currency_id': self.currency_id.id,
                    'partner_id': self.partner_id.id,
                    'token_id': token.id,
                    'operation': 'offline',
                    'tokenize': False,
                    'invoice_ids': [(4, self.id)]
                })

                tx_sudo.with_context({'from_authorize_custom': True, 'from_invoice_reauth': True})._send_payment_request()
                if tx_sudo.state == 'error':
                    error_msg = tx_sudo.state_message
                    self.write({'is_authorize_tx_failed': True})
            if error_msg:
                self.message_post(body=error_msg)



    def payment_action_capture(self):
        return super(AccountMove, self.with_context({'create_payment': True})).payment_action_capture()

    def cron_capture_autherize_invoices(self):

        payment_terms = self.env['account.payment.term'].search([('is_pre_payment', '=', True)])

        invoices = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('invoice_payment_term_id', 'in', payment_terms.ids),
            ('authorized_transaction_ids', '!=', False),
            ('invoice_date_due', '<=', fields.Date.today())])


        transactions = invoices.mapped('authorized_transaction_ids').filtered(lambda r: r.state == 'authorized')

        for transaction in transactions:
            transaction.action_capture()
        failed_txs = transactions.filtered(lambda r: r.state == 'error')
        if failed_txs:
            failed_txs.mapped('invoice_ids').write({'is_authorize_tx_failed': True})
            failed_txs.mapped('invoice_ids').message_post(body='Failed to capture transaction.')
