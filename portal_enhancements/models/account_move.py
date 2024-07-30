# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return 0 if count else self
        return super(AccountMove, self).search(args, offset, limit, order, count=count)

    @api.model_create_multi
    def create(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(AccountMove, self).create(vals)

    def write(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(AccountMove, self).write(vals)

    def unlink(self):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(AccountMove, self).unlink()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.move_id._name):
            return 0 if count else self
        return super(AccountMoveLine, self).search(args, offset, limit, order, count=count)

    @api.model_create_multi
    def create(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.move_id._name):
            return False
        return super(AccountMoveLine, self).create(vals)

    def write(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.move_id._name):
            return False
        return super(AccountMoveLine, self).write(vals)

    def unlink(self):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.move_id._name):
            return False
        return super(AccountMoveLine, self).unlink()
