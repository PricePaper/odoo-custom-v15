# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from odoo.tools import email_normalize
from odoo.exceptions import UserError
from odoo import api, fields, models, Command


class PortalWizardUser(models.TransientModel):

    _inherit = 'portal.wizard.user'


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

