# -*- coding: utf-8 -*-
from odoo import fields, models, api


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    sales_person_ids = fields.Many2many('res.partner', string="Sales Persons")

    @api.model
    def default_get(self, fields):
        """
        Auto Fill sales person ids in Convert To Opportunity Wizard
        """
        result = super(Lead2OpportunityPartner, self).default_get(fields)
        if self._context.get('default_sales_person_ids'):
            result['sales_person_ids'] = self._context.get('default_sales_person_ids')
        return result


    def action_apply(self):
        """
        Write Sales person ids to Lead record while Click on Create Opportunity button of wizard
        """
        self.ensure_one()
        if self.name != 'merge':
            leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))
            leads.write({'sales_person_ids': [(6, 0, self.sales_person_ids.ids)]})
        return super(Lead2OpportunityPartner, self).action_apply()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
