# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    portal_access = fields.Boolean(string='Give Portal Access',default=False)
    

    def _action_convert(self):
        """ """
        result_opportunities = super(Lead2OpportunityPartner,self)._action_convert()
        if self.portal_access:
            partner = result_opportunities.partner_id
            portal_wizard = self.env['portal.wizard'].create({
                'partner_ids':[(6,0,[partner.id])]
            })
            portal_wizard.user_ids.action_grant_access()
       
        return result_opportunities