# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    portal_access_level = fields.Selection([('manager', 'Manager'), ('user', 'Administrator')],
                                        string='Portal Access Level')
    portal_company_ids = fields.Many2many('res.partner', 'portal_company_partner_rel','res_partner_id', 'portal_partner_id',
                                          string="Accessible Companies", domain=[('is_company','=',True)])
    portal_partner_ids = fields.Many2many('res.partner', 'portal_company_partner_rel', 'portal_partner_id', 'res_partner_id',
                                          string="Portal Users", domain=[('is_company', '=', False)])

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        for key in ('portal_company_ids', 'portal_partner_ids'):
            if key in vals:
                self.clear_caches()
                break
        return res
