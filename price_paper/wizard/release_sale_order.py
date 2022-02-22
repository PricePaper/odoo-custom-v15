# -*- coding: utf-8 -*-

from odoo import models, api


class SaleOrderRelease(models.TransientModel):
    """
    This wizard release all the selected orders
    """

    _name = "release.sale.order"
    _description = "Release Cedit Hold sale orders"

    def release_order(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['sale.order'].browse(active_ids):
            record.action_release_credit_hold()
        return {'type': 'ir.actions.act_window_close'}


SaleOrderRelease()


class SalePriceHoldOrderRelease(models.TransientModel):
    """
    This wizard release all the selected price Hold orders price Hold
    """

    _name = "release.price.hold.sale.order"
    _description = "Release Price Hold sale orders"

    def release_order(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['sale.order'].browse(active_ids):
            record.action_release_price_hold()
        return {'type': 'ir.actions.act_window_close'}


SalePriceHoldOrderRelease()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
