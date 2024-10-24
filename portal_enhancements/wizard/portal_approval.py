# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _


class PortalApproval(models.TransientModel):
    _name = "portal.approval"
    _description = 'Wizard to give the Approve the documents submittion'


    business_registration_type = fields.Char(string='Business Registration')
    payment_type = fields.Char(string='Payment Type Chosen')
    business_resale_sign_document = fields.Many2one('sign.request',string='Resale Certificate')
    payment_credit_application = fields.Many2one('documents.document',string='Credit Application')
    tax_exempt_certifcate_id = fields.Many2one('documents.document',string='Tax Exempt Certificate Id')
    business_approval = fields.Boolean(string='Is Business Regitration Successful?',default=False)
    payment_approval = fields.Boolean(string='Is Payment method chosen approved?',default=False)
    rejection_reason = fields.Char(string='Rejection Reason')


    def validate_portal_access(self):
        if self.business_approval and self.payment_approval:
            active_oppr = self.env.context.get('active_ids', [])
            if active_oppr and active_oppr[0]:
                oppr = self.env['res.partner'].browse([active_oppr[0]])
                oppr.is_verified = True
                template_id = self.env['ir.config_parameter'].sudo().get_param('portal_enhancements.approval_email_template')
                template = self.env['mail.template'].sudo().browse(int(template_id))
                
                template.send_mail(oppr.id, force_send=True)
                
        else:
            active_oppr = self.env.context.get('active_ids', [])
            if active_oppr and active_oppr[0]:
                oppr = self.env['res.partner'].browse([active_oppr[0]])
                if not self.payment_approval:
                    oppr.business_verification_status = False
                if not self.business_approval:
                    oppr.businesss_registration_information = False

                oppr.rejection_reason = self.rejection_reason
                template_id = self.env['ir.config_parameter'].sudo().get_param('portal_enhancements.reject_email_template')
                template = self.env['mail.template'].sudo().browse(int(template_id))
                template.send_mail(oppr.id, force_send=True)

            return {'type': 'ir.actions.act_window_close'}
