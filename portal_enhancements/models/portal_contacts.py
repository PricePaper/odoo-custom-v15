# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):

    _name = 'portal.contacts'

    partner_id = fields.Many2one('res.partner',  string="Partner")
    name = fields.Char(string="Name", related="partner_id.name")
    parent_id = fields.Many2one('res.partner', string="Related Company")
    phone = fields.Char(string="Contacts", related="partner_id.phone")
    portal_partner_id = fields.Many2one('res.partner', string="Portal User")
    company_type = fields.Selection(related="partner_id.company_type", string="Company Type")