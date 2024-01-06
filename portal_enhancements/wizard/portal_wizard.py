# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from odoo.tools import email_normalize
from odoo.exceptions import UserError
from odoo import api, fields, models, Command


class PortalWizardUser(models.TransientModel):

    _inherit = 'portal.wizard.user'

    def action_grant_access(self):
        """Grant the portal access to the partner.
        If the partner has no linked user, we will create a new one in the same company
        as the partner (or in the current company if not set).

        An invitation email will be sent to the partner.
        Overridden to add user to Enhanced Portal Group
        """
        self.ensure_one()
        self._assert_user_email_uniqueness()

        if self.is_portal or self.is_internal:
            raise UserError(_('The partner "%s" already has the portal access.', self.partner_id.name))

        group_portal = self.env.ref('base.group_portal')
        group_public = self.env.ref('base.group_public')
        group_portal_enhanced = self.env.ref('portal_enhancements.group_portal_enhanced_record_access')

        # update partner email, if a new one was introduced
        if self.partner_id.email != self.email:
            self.partner_id.write({'email': self.email})

        user_sudo = self.user_id.sudo()

        if not user_sudo:
            # create a user if necessary and make sure it is in the portal group
            company = self.partner_id.company_id or self.env.company
            user_sudo = self.sudo().with_company(company.id)._create_user()

        if not user_sudo.active or not self.is_portal:
            user_sudo.write({'active': True, 'groups_id': [(4, group_portal.id), (3, group_public.id)]})
            # prepare for the signup process
            user_sudo.partner_id.signup_prepare()

        # grant enhanced portal access
        if self.is_portal and self.partner_id.portal_access_level and not user_sudo.has_group('portal_enhancements.group_portal_enhanced_record_access'):
            user_sudo.write({'active': True, 'groups_id': [(4, group_portal_enhanced.id)]})

        self.with_context(active_test=True)._send_email()

        return self.wizard_id._action_open_modal()

    def action_grant_access(self):
        """Grant the portal access to the partner.
        Inherited to add user to Enhanced Portal Group.
        """
        self.ensure_one()

        action = super(PortalWizardUser, self).action_grant_access()
        group_portal_enhanced = self.env.ref('portal_enhancements.group_portal_enhanced_record_access')

        user_sudo = self.user_id.sudo()
        if user_sudo:
            if self.is_portal and self.partner_id.portal_access_level in ['manager', 'user']:
                user_sudo.write({'groups_id': [(4, group_portal_enhanced.id)]})

        return action

    def action_revoke_access(self):
        """Remove the user of the partner from the portal group.
        If the user was only in the portal group, we archive it.

        Inherited to add user to Enhanced Portal Group.
        Upon revoking remove all groups, access rights, archive user
        """
        self.ensure_one()

        action = super(PortalWizardUser, self).action_revoke_access()

        user_sudo = self.user_id.sudo()
        if user_sudo:
            user_sudo.write({'groups_id': [(5, 0, 0)], 'active': False})

        return action

