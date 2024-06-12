# -*- coding: utf-8 -*-

from odoo import api, models, fields

from ...authorize_extension.authorize_request_custom import AuthorizeAPICustom
import re


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_partner_payment_methods(self, partner_id=None):

        result = []

        if partner_id is None or not isinstance(partner_id, int):
            return result

        partner = self.browse(partner_id)
        if partner:

            default_payment_term = partner.property_payment_term_id

            if default_payment_term:
                payment_terms = {
                    'payment_term': default_payment_term.name,
                    'payment_term_id': default_payment_term.id,
                    'payment_methods': []
                }

                if default_payment_term.payment_method == 'ach-debit':
                    payment_terms['payment_methods'] = [
                        {'name': 'Credit Card', 'availability': False, 'payment_acquirer': 'authorize', 'default': False},
                        {'name': 'COD', 'availability': False, 'payment_acquirer': 'cod', 'default': False},
                        {'name': 'ACH-Debit', 'availability': True, 'payment_acquirer': 'ach-debit', 'default': True}
                    ]
                elif default_payment_term.is_pre_payment:
                    payment_terms['payment_methods'] = [
                        {'name': 'Credit Card', 'availability': True, 'payment_acquirer': 'authorize', 'default': True},
                        {'name': 'COD', 'availability': False, 'payment_acquirer': 'cod', 'default': False},
                        {'name': 'ACH-Debit', 'availability': True, 'payment_acquirer': 'ach-debit', 'default': False}
                    ]
                elif default_payment_term.is_discount:
                    payment_terms['payment_methods'] = [
                        {'name': 'Credit Card', 'availability': True, 'payment_acquirer': 'authorize', 'default': False},
                        {'name': 'COD', 'availability': True, 'payment_acquirer': 'cod','default': True},
                        {'name': 'ACH-Debit', 'availability': False, 'payment_acquirer': 'ach-debit', 'default': False}
                    ]

                else:
                    payment_terms['payment_methods'] = [
                        {'name': 'Credit Card', 'availability': True, 'payment_acquirer': 'authorize', 'default': False},
                        {'name': 'COD', 'availability': True, 'payment_acquirer': 'cod', 'default': False},
                    ]
                result.append(payment_terms)

            return result

    @api.model
    def create_authorize_customer_profile(self, acquirer_id=None, partner_id=None):
        """
        Creates new customerProfileId with authorizenet, if profile exists returns profile id
        @param acquirer_id: Payment Acquirer
        @param partner_id: Partner
        @return: customerProfileId
        """

        def extract_duplicate_id(text_re):
            """
            Extracts the duplicate ID from the provided text.
            """
            match = re.search(r'ID (\d+)', text_re)
            if match:
                return match.group(1)
            return None

        result = []

        message = {'success': False,
                   'customerProfileId': False,
                   'error': False}

        if not all(isinstance(i, int) for i in [partner_id, acquirer_id]):
            message['error'] = "partner_id and acquirer_id must be integers"
            result.append(message)
            return result

        acquirer = self.env['payment.acquirer'].browse(acquirer_id).filtered(lambda rec: rec.provider == 'authorize')
        partner = self.browse(partner_id)

        if not acquirer.exists() or not partner.exists():
            message['error'] = "Partner or Acquirer does not exists"
            result.append(message)
            return result

        customer_profile_id = partner.payment_token_ids and partner.payment_token_ids[0].authorize_profile or ''
        if customer_profile_id:
            message['success'] = True
            message['customerProfileId'] = customer_profile_id
            result.append(message)
            return result

        authorize_api = AuthorizeAPICustom(acquirer)

        profile_response = authorize_api.create_customer_profile(partner)

        print("prof", profile_response)

        if profile_response.get('customerProfileId', False):
            message['success'] = True
            message['customerProfileId'] = profile_response.get('customerProfileId')

        elif 'err_code' and 'err_msg' in profile_response:

            if profile_response['err_code'] == 'E00039':
                duplicate_id = extract_duplicate_id(profile_response['err_msg'])

                if duplicate_id:
                    message['success'] = True
                    message['customerProfileId'] = duplicate_id
                    message['error'] = profile_response['err_msg']

        else:
            message['error'] = "Profile creation error\n{err_code}\n{err_msg}".format(**profile_response)
        result.append(message)
        return result





