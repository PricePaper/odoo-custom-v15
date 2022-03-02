# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrderCancel(models.TransientModel):
    _inherit = 'sale.order.cancel'

    reason = fields.Text(string='Reason', required=1)

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

    def action_cancel(self):
        reason = self.reason
        if self.order_id.cancel_reason:
            reason = "%s\n%s" % (self.order_id.cancel_reason, self.reason)
        self.order_id.write({'cancel_reason': reason})
        return self.order_id.with_context({'disable_cancel_warning': True, 'from_cancel_wizard': True}).action_cancel()


SaleOrderCancel()
