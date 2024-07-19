# -*- coding: utf-8 -*-

from odoo import api, models, fields
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

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

    @api.model
    def create_authorize_customer_payment_profile(self, acquirer_id=None, partner_id=None, address_id=False, opaqueData=False, is_default=False):
        """
        Checks for customer profile, creates new if not found,
        Creates new payment profile with encrypted card data,
        returns new payment.token

        @param is_default:
        @param opaqueData:
        @param acquirer_id:
        @param partner_id:
        @param address_id:
        @return: payment.token
        """

        result = []
        self = self.sudo()

        message = {'success': False,
                   'payment_token': False,
                   'error': False}

        if not all(isinstance(i, int) for i in [partner_id, acquirer_id]):
            message['error'] = "partner_id and acquirer_id  must be integers"
            result.append(message)
            return result
        if address_id:
            address_id = self.browse(address_id)
            if not address_id.exists():
                message['error'] = "Billing Address does not exists"
                result.append(message)
                return result

        if not opaqueData:
            message['error'] = "opequedata missing"
            result.append(message)
            return result

        acquirer = self.env['payment.acquirer'].browse(acquirer_id).filtered(lambda rec: rec.provider == 'authorize')
        partner = self.browse(partner_id)

        if not acquirer.exists() or not partner.exists():
            message['error'] = "Partner or Acquirer does not exists"
            result.append(message)
            return result

        customer_profile = self.create_authorize_customer_profile( acquirer_id=acquirer_id, partner_id=partner_id)

        if customer_profile[0].get('success', False):
            customer_profile_id = customer_profile[0].get('customerProfileId')
        else:
            message['error'] = customer_profile[0]['error']
            result.append(message)
            return message

        authorize_api = AuthorizeAPICustom(acquirer)

        payment_profile = authorize_api.create_payment_profile(customer_profile_id, partner, opaqueData, address_id)

        if not payment_profile.get('paymentProfile', {}).get('customerPaymentProfileId'):
            message['error'] = "Token creation error {err_code} {err_msg}".format(**payment_profile)
            result.append(message)
            return message

        payment_token = self.env['payment.token'].create({
                                    'acquirer_id': acquirer_id,
                                    'name': "%s - %s - %s" % (self.partner.name,
                                                              payment_profile.get('paymentProfile', {}).get('payment', {}).get('creditCard', {}).get(
                                                                  'cardType'),
                                                              payment_profile.get('paymentProfile', {}).get('payment', {}).get('creditCard', {}).get(
                                                                  'cardNumber').replace('X', '')),
                                    'partner_id': partner_id,
                                    'acquirer_ref': payment_profile.get('paymentProfile', {}).get('customerPaymentProfileId'),
                                    'authorize_profile': customer_profile_id,
                                    'authorize_payment_method_type': acquirer_id.authorize_payment_method_type,
                                    'verified': True,
                                    'card_type': payment_profile.get('paymentProfile', {}).get('payment', {}).get('creditCard', {}).get('cardType'),
                                    'address_id': address_id or partner_id,
                                    'is_default': is_default
                                })

        if payment_token:
            message['token'] = payment_token
            message['success'] = True
        result.append(message)
        return result


    def get_partner_delivery_date(self):
        partner_deliver_date = []
        for partner in self:
            shipping_date = date.today() + relativedelta(days=1)
            day_list = []
            if partner.change_delivery_days:
                if partner.delivery_day_mon:
                    day_list.append(0)
                if partner.delivery_day_tue:
                    day_list.append(1)
                if partner.delivery_day_wed:
                    day_list.append(2)
                if partner.delivery_day_thu:
                    day_list.append(3)
                if partner.delivery_day_fri:
                    day_list.append(4)
                if partner.delivery_day_sat:
                    day_list.append(5)
                if partner.delivery_day_sun:
                    day_list.append(6)
            else:
                if partner.zip_delivery_id:
                    if partner.zip_delivery_day_mon:
                        day_list.append(0)
                    if partner.zip_delivery_day_tue:
                        day_list.append(1)
                    if partner.zip_delivery_day_wed:
                        day_list.append(2)
                    if partner.zip_delivery_day_thu:
                        day_list.append(3)
                    if partner.zip_delivery_day_fri:
                        day_list.append(4)
                    if partner.zip_delivery_day_sat:
                        day_list.append(5)
                    if partner.zip_delivery_day_sun:
                        day_list.append(6)
            weekday = date.today().weekday()
            day_diff = 0
            if day_list:
                if any(weekday < i for i in day_list):
                    for i in day_list:
                        if weekday < i:
                            day_diff = i - weekday
                            break
                else:
                    day_diff = (6 - weekday) + day_list[0] + 1
                shipping_date = date.today() + relativedelta(days=day_diff)
            shipping_date = shipping_date.strftime("%Y-%m-%d")
            partner_deliver_date.append({'partner': partner.id, 'deliver_by': shipping_date})
        return partner_deliver_date
