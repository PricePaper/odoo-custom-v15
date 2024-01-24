# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    portal_access_level = fields.Selection([('manager', 'Manager'), ('user', 'Administrator')],
                                        string='Portal Access Level')
    portal_company_ids = fields.Many2many('res.partner', 'portal_company_partner_rel','res_partner_id', 'portal_partner_id',
                                          string="Accessible Companies", domain=[('is_company','=',True)], tracking=True)
    portal_partner_ids = fields.Many2many('res.partner', 'portal_company_partner_rel', 'portal_partner_id', 'res_partner_id',
                                          string="Portal Users", domain=[('is_company', '=', False)])
    has_portal_access = fields.Boolean(string="Portal Access", compute="_compute_portal_access")

    portal_contact_ids = fields.One2many('portal.contacts', 'portal_partner_id', string="Accessible Contacts")

    def write(self, vals):
        current_company_ids = self.portal_company_ids

        res = super(ResPartner, self).write(vals)

        if 'portal_company_ids' in vals:
            removed_companies = current_company_ids - self.portal_company_ids
            added_companies = self.portal_company_ids - current_company_ids
            if removed_companies:
                remove_contacts = self.portal_contact_ids.filtered(lambda x: x.partner_id.id in removed_companies.ids or x.parent_id.id in removed_companies.ids)
                remove_contacts.unlink()

                removed_company_names = '<li>' + '</li><li>'.join(removed_companies.mapped('name')) + '</li>'
                self.message_post(body=f"Companies Removed:<br/><ul><span style='color: red;'>{removed_company_names}</span></ul>")

            if added_companies:
                self.portal_contact_ids = [(0, 0, {'partner_id': company.id}) for company in added_companies]
                added_company_names = '<li>' + '</li><li>'.join(added_companies.mapped('name')) + '</li>'
                self.message_post(
                    body=f'Companies Added:<br/><ul><span style="color: green;">{added_company_names}</span></ul>')

        for key in ('portal_company_ids', 'portal_partner_ids', 'portal_contact_ids'):
            if key in vals:
                self.clear_caches()
                break
        return res

    def _compute_portal_access(self):
        for partner in self:
            if partner.user_ids:
                user_id = partner.user_ids[0]
                partner.has_portal_access = user_id and all(user_id.has_group(group) for group in ('base.group_portal', 'portal_enhancements.group_portal_enhanced_record_access'))
            else:
                partner.has_portal_access = False

    def action_add_contacts(self):

        origin_id = self._context.get('origin_id', None)
        if self._context.get('origin_model', None) == 'res.partner' and origin_id:

            contact_ids = self.env['res.partner'].browse([origin_id]).portal_contact_ids.filtered(lambda x: x.parent_id.id == self.id).partner_id
            print(contact_ids)

            wizard_id = self.env['add.portal.contacts'].create({'company_id': self.id,
                                                             'portal_wizard_contact_ids': [(6, 0, contact_ids.ids)]})

            return {
                'name': _("Add Contacts"),
                'view_mode': 'form',
                'res_model': 'add.portal.contacts',
                'res_id': wizard_id.id,
                'type': 'ir.actions.act_window',
                'domain': [()],
                'target': 'new',
            }
        return False
