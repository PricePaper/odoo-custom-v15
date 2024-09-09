from odoo import models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    '''state change in loyalty.transaction according to payment state'''

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        # Call the method to update loyalty transaction state after payments are created
        invoices = self.env['account.move'].browse(self._context.get('active_ids', []))
        print("invoicessss = ", invoices)
        invoices._update_loyalty_transaction_state()
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _update_loyalty_transaction_state(self):
        # Find all sale orders related to these invoices
        sale_orders = self.env['sale.order'].search([('invoice_ids', 'in', self.ids)])

        for order in sale_orders:
            invoices = order.invoice_ids
            total_invoice_amount = sum(invoice.amount_total for invoice in invoices)
            print("total invoice amount = ", total_invoice_amount)
            rounded_total_invoice_amount = round(total_invoice_amount, 2)
            print("round total invoice amount",rounded_total_invoice_amount)
            rounded_order_amount_total = round(order.amount_total, 2)
            is_amount_match = rounded_total_invoice_amount == rounded_order_amount_total
            print("is amount match = ",is_amount_match)
            all_in_payment_or_paid = all(
                invoice.payment_state in ['in_payment'] for invoice in invoices
            )
            print("all in payment",all_in_payment_or_paid)

            if is_amount_match and all_in_payment_or_paid:
                loyalty_transactions = self.env['loyalty.transaction'].search([('order_id', '=', order.id)])
                print('Related loyalty transactions:', loyalty_transactions)
                for transaction in loyalty_transactions:
                    if transaction.state == 'pending' or transaction.state == 'draft':
                        transaction.state = 'confirmed'
                        print('Loyalty transaction updated:', transaction)
