from odoo import fields, models, api, _
from odoo.exceptions import UserError

from odoo.addons import decimal_precision as dp


class CashCollectedLines(models.Model):
    _inherit = 'cash.collected.lines'

    discount = fields.Float(string='Discount(%)')
    discount_amount = fields.Float(string='Discount', digits='Product Price')

    # Note detailed testing pending in all the below functionalities,do this after batch_delivery and price paper completion
    def check_discount_validity(self, amount, discount_per=False, discount_amount=False):
        customer_discount_per = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_extension.customer_discount_limit', 5.00)
        if isinstance(customer_discount_per, str):
            customer_discount_per = float(customer_discount_per)
        discount_amount_limit = round(amount * (customer_discount_per / 100), 2)
        if customer_discount_per and (customer_discount_per < discount_per or discount_amount_limit < discount_amount):
            raise UserError(_('Cannot add discount more than {}%.'.format(customer_discount_per)))
        return True

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id:
            self.amount = self.invoice_id.amount_total
            days = (self.invoice_id.invoice_date - fields.Date.context_today(self)).days
            if self.invoice_id.invoice_payment_term_id.is_discount and abs(
                    days) < self.invoice_id.invoice_payment_term_id.due_days:
                discount_per = self.invoice_id.invoice_payment_term_id.discount_per
                discount_amount = self.invoice_id.amount_residual_signed * (self.discount / 100)
                self.check_discount_validity(self.invoice_id.amount_residual_signed, discount_per=discount_per,
                                             discount_amount=discount_amount)
                self.discount = self.invoice_id.invoice_payment_term_id.discount_per
                self.discount_amount = discount_amount
                self.amount = self.invoice_id.amount_residual_signed - discount_amount
            else:
                self.discount = 0

    @api.onchange('discount')
    def onchange_discount(self):
        if self.invoice_id:
            self.check_discount_validity(self.invoice_id.amount_residual_signed, discount_per=self.discount)
            self.discount_amount = round(self.invoice_id.amount_residual_signed * (self.discount / 100), 2)
            self.amount = self.invoice_id.amount_residual_signed - self.discount_amount

    @api.onchange('discount_amount')
    def onchange_discount_amount(self):
        if self.invoice_id:
            self.check_discount_validity(self.invoice_id.amount_residual_signed, discount_amount=self.discount_amount)
            self.discount = round((self.discount_amount / self.invoice_id.amount_residual_signed) * 100, 2)
            self.amount = self.invoice_id.amount_residual_signed - self.discount_amount

    def create_from_common_batch_payment(self):

        batch_payment_info = {}

        for line in self:
            if not line.amount:
                continue

            need_writeoff = True if line.discount else False

            if need_writeoff and not self.env.user.company_id.discount_account_id:
                raise UserError(_('Please set a discount account in company.'))
            if line.invoice_id:
                am_rec = self.env['account.move']
                if line.invoice_id and line.discount_amount:
                    line.invoice_id.write({'discount_from_batch': line.discount_amount})
                    am_rec = line.invoice_id.with_context(batch_discount=True).create_discount_writeoff()
                batch_payment_info.setdefault(line.journal_id, {}). \
                    setdefault(line.payment_method_line_id, []). \
                    append({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_line_id': line.payment_method_line_id.id,
                    'partner_id': line.partner_id.id,
                    'amount': line.amount,
                    'journal_id': line.journal_id.id,
                    'invoice_ids': [(6, 0, line.invoice_id.ids)],
                    'communication': line.communication,
                    'common_batch_id': line.common_batch_id.id,
                    'discount_amount': line.discount_amount,
                    'discount_journal_id': am_rec.id if am_rec else False
                })

            else:
                batch_payment_info.setdefault(line.journal_id, {}). \
                    setdefault(line.payment_method_line_id, []). \
                    append({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_line_id': line.payment_method_line_id.id,
                    'partner_id': line.partner_id.id,
                    'amount': line.amount,
                    'journal_id': line.journal_id.id,
                    'communication': line.communication,
                    'common_batch_id': line.common_batch_id.id,
                })

        AccountBatchPayment = self.env['account.batch.payment']

        for journal, batch_vals in batch_payment_info.items():
            for payment_method, payment_vals in batch_vals.items():
                AccountBatchPayment.create({
                    'batch_type': 'inbound',
                    'journal_id': journal.id,
                    'payment_ids': [(0, 0, vals) for vals in payment_vals],
                    'payment_method_line_id': payment_method.id,
                })

    def create_payment(self):
        print('acc ext')
        batch_payment_info = {}

        for line in self:
            if not line.amount:
                continue

            need_writeoff = True if line.discount else False

            if need_writeoff and not self.env.user.company_id.discount_account_id:
                raise UserError('Please choose a discount account in company.')
            print(line.invoice_id, line.discount_amount)
            if line.invoice_id:
                am_rec = self.env['account.move']
                if line.invoice_id and line.discount_amount:
                    line.invoice_id.write({'discount_from_batch': line.discount_amount})
                    am_rec = self.env['add.discount'].with_context(active_id=line.invoice_id.id).create_truck_discount(batch_discount=line.discount_amount)
                batch_payment_info.setdefault(line.journal_id, {}).setdefault(line.payment_method_line_id, []).append({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_line_id': line.payment_method_line_id.id,
                    'partner_id': line.partner_id.id,
                    'amount': line.amount,
                    'journal_id': line.journal_id.id,
                    'invoice_id': line.invoice_id,
                    'ref': line.communication,
                    'batch_id': line.batch_id.id,
                    'discount_amount': line.discount_amount,
                    'discount_journal_id': am_rec.id if am_rec else False
                })
            else:
                batch_payment_info.setdefault(line.journal_id, {}).setdefault(line.payment_method_line_id, []).append({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_line_id': line.payment_method_line_id.id,
                    'partner_id': line.partner_id.id,
                    'amount': line.amount,
                    'journal_id': line.journal_id.id,
                    'ref': line.communication,
                    'batch_id': line.batch_id.id,
                })
        for journal, batch_vals in batch_payment_info.items():
            for payment_method, payment_vals in batch_vals.items():
                batch_id = self.env['account.batch.payment'].create({
                    'batch_type': 'inbound',
                    'journal_id': journal.id,
                    'payment_method_id': payment_method.payment_method_id.id,
                })
                for vals in payment_vals:
                    invoice_id = vals.pop('invoice_id', False)
                    vals['batch_payment_id'] = batch_id.id
                    payment = self.env['account.payment'].create(vals)

                    payment.action_post()
                    if invoice_id:
                        vals['batch_payment_id'] = batch_id.id
                        line = invoice_id.line_ids.filtered(
                            lambda rec: rec.account_internal_type in ('receivable', 'payable') and \
                                        not rec.currency_id.is_zero(rec.amount_residual_currency))
                        line |= payment.line_ids.filtered(
                            lambda rec: rec.account_internal_type == line.account_internal_type)
                        line.reconcile()




class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_discount_limit = fields.Float(
        string='Customer Discount Limit',
        config_parameter='accounting_extension.customer_discount_limit',
        default=5.0
    )
