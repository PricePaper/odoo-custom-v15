# -*- encoding: utf-8 -*-

from odoo import api, fields, models


class SaleTeamRegisterPayment(models.TransientModel):
    _name = "sale.team.register.payment"
    _description = "Register Payment"

    partner_id = fields.Many2one("res.partner", string="Customer")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.user.company_id.currency_id.id)
    amount = fields.Monetary(string="Amount", currency_field="currency_id")
    payment_date = fields.Date(string="Payment Date", default=fields.Date.context_today)
    journal_id = fields.Many2one("account.journal", string="Payment Journal")
    reference = fields.Char(string="Reference")

    @api.model
    def default_get(self, fields):
        res = super(SaleTeamRegisterPayment, self).default_get(fields)
        cash_journal = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
        res['journal_id'] = cash_journal and cash_journal.id or False
        return res


    def action_register_payment(self):
        self.ensure_one()
        payment_method = self.env.ref('account.account_payment_method_manual_in')
        self.env['account.payment'].sudo().create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            'ref': self.reference,
            'payment_method_id': payment_method and payment_method.id,
        })
        return True



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
