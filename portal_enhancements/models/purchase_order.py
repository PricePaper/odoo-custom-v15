# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return 0 if count else self
        return super(PurchaseOrder, self).search(args, offset, limit, order, count=count)

    @api.model
    def create(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(PurchaseOrder, self).create(vals)

    def write(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(PurchaseOrder, self).write(vals)

    def unlink(self):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(PurchaseOrder, self).unlink()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.order_id._name):
            return 0 if count else self
        return super(PurchaseOrderLine, self).search(args, offset, limit, order, count=count)

    @api.model
    def create(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.order_id._name):
            return False
        return super(PurchaseOrderLine, self).create(vals)

    def write(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.order_id._name):
            return False
        return super(PurchaseOrderLine, self).write(vals)

    def unlink(self):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.order_id._name):
            return False
        return super(PurchaseOrderLine, self).unlink()
