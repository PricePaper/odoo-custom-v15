# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning

class SignRequestItem(models.Model):
    _inherit='sign.request.item'

    is_business_registration = fields.Boolean(string='Business Registration',default=False)
    is_credit_application = fields.Boolean(string='Credit Application',default=False)



    def action_completed(self):
        for rec in self:
            if rec.is_business_registration:
                rec.partner_id.businesss_registration_information = True
                if rec.partner_id.basic_verification_submit and rec.partner_id.businesss_registration_information:
                    rec.partner_id.business_verification_status = 'submit'
                    rec.partner_id.create_helpdesk_ticket_approval()
                rec.partner_id.sign_request_business = rec.sign_request_id.id
            if rec.is_credit_application:
                rec.partner_id.business_verification_status = 'submit'
                rec.partner_id.create_helpdesk_ticket_approval()
        return super(SignRequestItem,self).action_completed()
