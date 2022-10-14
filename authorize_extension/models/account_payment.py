from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    card_payment_type = fields.Selection(selection=[('bank', "Direct Bank"), ('authorize', "Through Authorize"), ], string="Card Swipe Payment Type")

    def _prepare_payment_transaction_vals(self, **extra_create_values):
        res = super(AccountPayment, self)._prepare_payment_transaction_vals(**extra_create_values)
        count = self.env['payment.transaction'].search_count([('reference', 'ilike', res['reference'])])
        if count > 0:
            res['reference'] = "%s-%s" % (res['reference'], count)
        return res


AccountPayment()


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _reconcile_payments(self, to_process, edit_mode=False):
        res = super(AccountPaymentRegister, self)._reconcile_payments(to_process, edit_mode)
        for vals in to_process:
            payment = vals['payment']
            if payment.payment_transaction_id and payment.reconciled_invoice_ids:
                if payment.reconciled_invoice_ids not in payment.payment_transaction_id.invoice_ids:
                    payment.payment_transaction_id.write({
                        'invoice_ids': [(4, inv.id) for inv in payment.reconciled_invoice_ids if
                                        inv not in payment.payment_transaction_id.invoice_ids],
                        'sale_order_ids': [(4, sale.id) for sale in
                                           payment.reconciled_invoice_ids.mapped('invoice_line_ids').mapped('sale_line_ids.order_id') if
                                           sale not in payment.payment_transaction_id.sale_order_ids]
                    })
        return res


AccountPaymentRegister()
