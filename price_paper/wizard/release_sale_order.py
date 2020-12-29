# -*- coding: utf-8 -*-

from odoo import models, api


class SaleOrderRelease(models.TransientModel):
    """
    This wizard release all the selected orders
    """

    _name = "release.sale.order"
    _description = "Release sale orders"

    @api.multi
    def release_order(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['sale.order'].browse(active_ids):
            record.action_ready_to_release()
        return {'type': 'ir.actions.act_window_close'}


SaleOrderRelease()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
