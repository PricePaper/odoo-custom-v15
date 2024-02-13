# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AddPortalContacts(models.TransientModel):

    _name = "add.portal.companies"

    portal_wizard_company_ids = fields.Many2many('res.partner', string="Contacts")
    parent_id = fields.Many2one('res.partner', string="Company", readonly=True)
    portal_user_id = fields.Many2one('res.partner', string="Portal User", readonly=True)

    def action_add_companies_to_portal_user(self):
        if self.portal_wizard_company_ids:
            self.portal_user_id.portal_company_ids = self.portal_wizard_company_ids
        else:
            self.portal_user_id.portal_company_ids = None
