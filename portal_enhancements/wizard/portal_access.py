# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class PortalAccess(models.TransientModel):

    _name = "portal.access"
    _description = 'Wizard to give the portal access to user'

    portal_user = fields.Many2one('res.partner', string='Portal User')
    create_new_user = fields.Boolean(string='Create New User', default=False)
    contact_name = fields.Char(string='Contact Name')
    contact_email = fields.Char(string='Contact Email')

    def validate_portal_access(self):
        if not self.portal_user and not self.create_new_user:
            raise UserError('Kindly Select Appropriate option')
        oppr = False
        model_xml_ids = {
            "sale.model_sale_order": True,
            "account.model_account_move": True,
            "purchase.model_purchase_order": False,
            "crm.model_crm_lead": False,
            "project.model_project_project": False,
            "helpdesk.model_helpdesk_ticket": True,
            "calendar.model_calendar_event": False
        }
        active_oppr = self.env.context.get('active_ids', [])
        if active_oppr and active_oppr[0]:
            oppr = self.env['crm.lead'].browse([active_oppr[0]])
        main_company = oppr.partner_id
        if main_company.parent_id:
            main_company = main_company.parent_id
            main_company.customer = True
        if self.portal_user and oppr:
            self.portal_user.portal_company_ids = [(4, main_company.id)]
            oppr.portal_user = self.portal_user.id
        if self.create_new_user:
            partner_id = main_company.copy()
            partner_id.portal_model_access.sudo().unlink()
            partner_id.write({
                'portal_access_level': 'user',
                'is_company': False,
                'portal_model_access': [(0, 0, {'model_id': self.env.ref(model).id, 'is_model_accessible': value}) for model, value in model_xml_ids.items()],
                'portal_company_ids': [(6, 0, [main_company.id])],
                'name':self.contact_name,
                'email':self.contact_email
            })
            portal_wizard = self.env['portal.wizard'].sudo().create({'partner_ids':[(6,0,[int(partner_id.id)])]})
            portal_wizard.user_ids.action_grant_access()
            oppr.portal_user = partner_id.id

        return {'type': 'ir.actions.act_window_close'}
