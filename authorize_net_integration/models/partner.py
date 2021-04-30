# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _get_profile_id(self):
        """
            Get profile id
            @param partner: browse record object of res.partner
            return : longint profile id
        """
        if not self:
            return False
        profile_id = self.profile_id or self.parent_id and self.parent_id.profile_id
        return profile_id

    @api.model
    def _get_profile(self, profile_id):
        if not profile_id:
            return False
        authorize_obj = self.env['authorizenet.api']
        login, key, url = authorize_obj._get_credentials()
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
            <getCustomerProfileRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                <merchantAuthentication>
                    <name>%s</name>
                    <transactionKey>%s</transactionKey>
                </merchantAuthentication>
                <customerProfileId>%s</customerProfileId>
            </getCustomerProfileRequest>""" % (login, key, profile_id)

        success, response, header, code = authorize_obj.execute_request(auth_data, url=url,
                                                                        headers={'Content-Type': 'text/xml'})

        if not success:
            code, message = authorize_obj._get_error_message(response)
            if code or message:
                raise UserError('Authorize.Net Warning-%s\n%s' % (code, message))
        return response

    @api.model
    def _create_authorizenet_profile(self):
        """
            Create Authorize net profile
            @param partner: browse record object of res.partner
            return : longint profile id
        """
        partner = self
        if not partner:
            return False
        authorize_obj = self.env['authorizenet.api']
        login, key, url = authorize_obj.get_credentials()
        cust_id = '%s-erp' % (partner.id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
            <createCustomerProfileRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                <merchantAuthentication>
                    <name>%s</name>
                    <transactionKey>%s</transactionKey>
                </merchantAuthentication>                        
                <profile>
                    <merchantCustomerId>%s</merchantCustomerId>
                    <email>%s</email>                                    
                </profile>
            </createCustomerProfileRequest>
            """ % (login, key, cust_id, partner.email)

        success, response, header, code = authorize_obj.execute_request(auth_data, url=url,
                                                                        headers={'Content-Type': 'text/xml'})

        if not success:
            code, message = authorize_obj._get_error_message(response)
            if code or message:
                raise UserError('Authorize.Net Warning-%s\n%s' % (code, message))
        profile_id = authorize_obj._get_profile_id(response)
        #        cursor = pooler.get_db(cr.dbname).cursor()
        partner.write({'profile_id': profile_id})
        #        cursor.commit()
        #        cursor.close()
        return profile_id


ResPartner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
