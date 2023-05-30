# -*- coding: utf-8 -*-


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    
    create_sample = fields.Boolean(string='Create Sample Request')
    sample_product_ids = fields.Many2many('product.product',string='Sample Products')


    def action_apply(self):
        if self.name == 'merge':
            result_opportunity = self._action_merge()
        else:
            result_opportunity = self._action_convert()

        if self.action !='nothing' and self.create_sample and self.sample_product_ids:
            sample_vals = {
                'partner_id':result_opportunity.partner_id.id,
                'partner_shipping_id':result_opportunity.partner_id.id,
                'request_lines':[(0,0,{'product_id':product.id}) for product in self.sample_product_ids],
                'lead_id':result_opportunity.id
            }
            sample_request = self.env['sample.request'].create(sample_vals)
            result_opportunity.sample_request_id = sample_request.id


        return result_opportunity.redirect_lead_opportunity_view()
