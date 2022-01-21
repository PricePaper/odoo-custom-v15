# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrderCancel(models.TransientModel):
    _name = 'so.cancel.reason'
    _description = "SO cancel reason"

    reason = fields.Text(string='Reason')

    def cancel_so(self):
        """
        Cancel SO and add the reason to it
        """

        order = self.env['sale.order'].browse(self._context.get('active_id'))
        reason = self.reason
        if order.cancel_reason:
            reason = order.cancel_reason + '\n' + self.reason
        order.cancel_reason = reason
        order.with_context(from_cancel_wizard=True).action_cancel()


SaleOrderCancel()
