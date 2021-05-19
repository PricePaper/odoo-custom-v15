# -*- coding: utf-8 -*-

from odoo import models, api


class OrderPointReset(models.TransientModel):
    """
    This wizard Reset Order Point
    """

    _name = "order.point.reset"
    _description = "Reset Order point"

    @api.multi
    def reset_order_point(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['product.product'].browse(active_ids):
            record.reset_orderpoint()
        return {'type': 'ir.actions.act_window_close'}


OrderPointReset()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
