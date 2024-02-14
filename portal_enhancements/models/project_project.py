# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning


class Project(models.Model):
    _inherit = "project.project"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return 0 if count else self
        return super(Project, self).search(args, offset, limit, order, count=count)

    @api.model
    def create(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(Project, self).create(vals)

    def write(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(Project, self).write(vals)

    def unlink(self):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self._name):
            return False
        return super(Project, self).unlink()


class Task(models.Model):
    _inherit = "project.task"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.project_id._name):
            return 0 if count else self
        return super(Task, self).search(args, offset, limit, order, count=count)

    @api.model
    def create(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.project_id._name):
            return False
        return super(Task, self).create(vals)

    def write(self, vals):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.project_id._name):
            return False
        return super(Task, self).write(vals)

    def unlink(self):
        partner_id = self.env.user.partner_id
        if partner_id.portal_access_level and not partner_id._check_portal_model_access(self.project_id._name):
            return False
        return super(Task, self).unlink()