# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning



class Meeting(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return 0 if count else self
        return super(Meeting, self).search(args, offset, limit, order, count=count)

    @api.model
    def create(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(Meeting, self).create(vals)

    def write(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(Meeting, self).write(vals)

    def unlink(self):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(Meeting, self).unlink()