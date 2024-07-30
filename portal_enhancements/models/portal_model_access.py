# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PortalModelAccessConfig(models.Model):
    _name = 'portal.model.access.config'

    model_id = fields.Many2one('ir.model', string="Model")
    name = fields.Char(string='Model Name')


class PortalModelAccess(models.Model):
    _name = 'portal.model.access'

    portal_partner_id = fields.Many2one('res.partner', string="Portal Partner")
    model_id = fields.Many2one('ir.model', string="Model")
    name = fields.Char(string='Model', related='model_id.display_name')

    is_model_accessible = fields.Boolean(string="Grant Access")
