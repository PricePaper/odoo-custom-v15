# -*- coding: utf-8 -*-

from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):

    def _prepare_quotations_domain(self, partner):
        # overridden to modify domain
        return [
            '|',('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('partner_id', 'in', partner.portal_company_ids.ids),
            ('state', 'in', ['sent', 'cancel'])
        ]

    def _prepare_orders_domain(self, partner):
        # overridden to modify domain
        return [
            '|', ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('partner_id', 'in', partner.portal_company_ids.ids),
            ('state', 'in', ['sale', 'done'])
        ]