# -*- coding: utf-8 -*-


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

class CrmLEad(models.Model):
    _inherit='crm.lead'
    portal_user = fields.Many2one('res.partner',string='Portal User')
    parent_company = fields.Many2one('res.partner',related='partner_id.parent_id')
    crm_hide_stages = fields.Many2many('crm.stage',related='company_id.crm_hide_stages')


    hide_acess = fields.Boolean(compute='_check_portal',store=True)

    @api.depends('stage_id','crm_hide_stages')
    def _check_portal(self):
        for rec in self:
            
            if rec.stage_id.id in rec.crm_hide_stages.ids:
                rec.hide_acess = True
            else:
                rec.hide_acess = False


    

    def action_view_portal_view(self):
        action = self.env['ir.actions.actions']._for_xml_id(
            'portal_enhancements.action_res_partner_portal_enhancements')
        action['domain'] = [('id', '=', self.portal_user.id), ('portal_access_level', '!=', False)]
        
        return action


    def open_create_portal(self):
        if not self.partner_id:
            raise UserError('No Customer is assigned to give portal access')
        
        partner = self.env['res.partner'].sudo().search([('email','=',self.email_from),('portal_access_level', '!=', False)],limit=1)
        contact_name = self.contact_name if self.contact_name else  self.partner_id.name,
        return {
            'name': 'Portal Access',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'portal.access',
            'target':'new',
            'context':{
                'default_portal_user':partner.id,
                'default_contact_name':contact_name,
                'default_contact_email':self.email_from
            }
            # 'res_id': self.id,
        }
        


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'
    
    create_portal = fields.Boolean(string='Give Portal Access',default=True)
    portal_user = fields.Many2one('res.partner',string='Portal User')
    
    @api.model
    def default_get(self, fields):
        vals = super(Lead2OpportunityPartner, self).default_get(fields)
        active_oppr = self.env.context.get('active_ids', [])
        if active_oppr:
            for rec in active_oppr:
                oppr = self.env['crm.lead'].browse([rec])
                partner = self.env['res.partner'].sudo().search([('email','=',oppr.email_from),('portal_access_level', '!=', False)],limit=1)
                
                if partner:
                    vals['portal_user'] = partner.id
                    break
       

        return vals



    def action_apply(self):
        if self.name == 'merge':
            result_opportunity = self._action_merge()
        else:
            result_opportunity = self._action_convert()

        if self.action =='create' and self.create_portal:
            main_company = result_opportunity.partner_id
            if main_company.parent_id:
                main_company = main_company.parent_id
            child_partner = main_company.child_ids
            if self.portal_user:
                self.portal_user.portal_company_ids = [(4,main_company.id)]
                result_opportunity.portal_user = self.portal_user.id

            else:
                if child_partner:
                    child_partner = child_partner[0]
                    child_partner.parent_id = False
                else:
                    child_partner = main_company.copy()

                model_xml_ids = {
                    "sale.model_sale_order":True, 
                    "account.model_account_move":True, 
                    "purchase.model_purchase_order":False, 
                    "crm.model_crm_lead":False,
                    "project.model_project_project":False, 
                    "helpdesk.model_helpdesk_ticket":True, 
                    "calendar.model_calendar_event":False
                }
                child_partner.portal_model_access.sudo().unlink()
                child_partner.write({
                    'portal_access_level' :'user',
                    'is_company':False,
                    'portal_model_access':[(0, 0, {'model_id': self.env.ref(model).id, 'is_model_accessible': value}) for model,value in model_xml_ids.items()],
                    'portal_company_ids':[(6,0,[main_company.id])]
                })
                portal_wizard = self.env['portal.wizard'].sudo().create({'partner_ids':[(6,0,[int(child_partner.id)])]})
                portal_wizard.user_ids.action_grant_access()
                result_opportunity.portal_user = child_partner.id

        if result_opportunity.sample_request_id and result_opportunity.partner_id:
            result_opportunity.sample_request_id.partner_id = result_opportunity.partner_id.parent_id.id or result_opportunity.partner_id.id
        else: 
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
