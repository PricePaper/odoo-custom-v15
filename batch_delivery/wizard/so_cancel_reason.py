# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrderCancel(models.TransientModel):
    _inherit = 'sale.order.cancel'

    reason = fields.Text(string='Reason', required=1)

    def action_cancel(self):
        """
        post cancel reason in SO.
        """
        self.order_id.message_post(body='Cancel Reason : ' + self.reason)
        return self.order_id.with_context({'disable_cancel_warning': True, 'from_cancel_wizard': True}).action_cancel()


SaleOrderCancel()
