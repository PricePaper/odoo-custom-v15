# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning


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

    portal_model_access = fields.One2many('portal.model.access', 'portal_partner_id',
                                          string="Manage Model Access Rights")
    portal_admin_id = fields.Many2one('res.partner', string="Related Administrator", domain=[('portal_access_level','=','user')])
    portal_manager_ids = fields.One2many('res.partner', 'portal_admin_id', string="Managers", domain=[('portal_access_level','=','manager')])



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

            if removed_companies and self.child_ids:
                for child in self.child_ids:
                    child.portal_company_ids = child.portal_company_ids - removed_companies

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

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.portal_access_level and self.parent_id:
            company_list = []
            for company in self.portal_company_ids:
                if company._origin not in self.parent_id.portal_company_ids:
                    company_list.append(company.display_name)
            if company_list:
                raise UserError(_(f"To designate the selected user as a Portal Administrator, please ensure that they have "
                              f"access to the following companies first.\n"+'\n'.join(company for company in company_list)))

    @api.onchange('portal_access_level')
    def _onchange_portal_access_level(self):
        if self.portal_access_level == 'user' and self.parent_id:
            self.parent_id = False
            return {
                'warning': {
                    'title': 'Warning!',
                    'message': 'Changing the "Portal Access Level" from "Manager" to "Administrator" will remove the currently assigned Administrator.'
                }
            }

    def action_add_companies(self):

        wizard_id = self.env['add.portal.companies'].create({'parent_id': self.parent_id.id, 'portal_user_id': self.id,
                                                             'portal_wizard_company_ids': [(6, 0, self.portal_company_ids.ids)]})
        ctx = dict(self._context)
        ctx.update({'related_companies': self.parent_id.portal_company_ids.ids})
        return {
            'name': _("Add Companies"),
            'view_mode': 'form',
            'res_model': 'add.portal.companies',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'domain': [()],
            'context': ctx,
            'target': 'new',
        }

    @api.model
    def default_get(self, fields):

        model_xml_ids = ["sale.model_sale_order", "account.model_account_move", "purchase.model_purchase_order", "crm.model_crm_lead",
                         "project.model_project_project", "helpdesk.model_helpdesk_ticket", "calendar.model_calendar_event"]
        res = super(ResPartner, self).default_get(fields)
        if 'portal_model_access' in fields:
            res['portal_model_access'] = [(0, 0, {'model_id': self.env.ref(model).id, 'is_model_accessible': False}) for model in model_xml_ids]
        return res

    def _check_portal_model_access(self, model: str):
        access_record = self.portal_model_access.filtered(lambda x: x.model_id.model == model)
        if access_record and access_record.is_model_accessible:
            return True
        return False

    def name_get(self):
        res = super(ResPartner, self).name_get()
        result = []
        for partner in res:
            partner_id = self.env['res.partner'].browse(partner[0])
            if partner_id.portal_access_level:
                result.append((partner[0], partner_id.name + ' - Portal User\n'))
            else:
                result.append((partner[0], partner[1]))

        return result


