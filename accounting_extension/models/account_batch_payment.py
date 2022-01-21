from odoo import fields, models, api


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    def action_batch_reconcile(self):
        for batch in self:
            if batch.payment_ids and all(pay.is_matched and pay.is_move_sent for pay in batch.payment_ids):
                batch.state = 'reconciled'
