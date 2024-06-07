# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning

class SignRequestItem(models.Model):
    _inherit='sign.request.item'

    is_business_registration = fields.Boolean(string='Business Registration',default=False)
    is_credit_application = fields.Boolean(string='Credit Application',default=False)



    def action_completed(self):
        import pdb
        pdb.set_trace()
        for rec in self:
            if rec.is_business_registration:
                rec.partner_id.businesss_registration_information = True
            if rec.is_credit_application:
                rec.partner_id.business_verification_status = 'submit'
        return super(SignRequestItem,self).action_completed()