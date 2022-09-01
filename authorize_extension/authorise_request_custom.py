import json
import logging
import pprint
from uuid import uuid4
import requests

_logger = logging.getLogger(__name__)


class AuthorizeAPICustom:

    def __init__(self, acquirer):
        """Initiate the environment with the acquirer data.

        :param recordset acquirer: payment.acquirer account that will be contacted
        """
        if acquirer.state == 'enabled':
            self.url = 'https://api.authorize.net/xml/v1/request.api'
        else:
            self.url = 'https://apitest.authorize.net/xml/v1/request.api'

        self.state = acquirer.state
        self.name = acquirer.authorize_login
        self.transaction_key = acquirer.authorize_transaction_key
        self.payment_method_type = acquirer.authorize_payment_method_type

    def _make_request(self, operation, data=None):
        """
        End point to communicate with authorize.net
        """
        request = {
            operation: {
                'merchantAuthentication': {
                    'name': self.name,
                    'transactionKey': self.transaction_key,
                },
                **(data or {})
            }
        }
        #todo remove logger to avoid printing sensitive informations
        _logger.info("sending request to %s:\n%s", self.url, pprint.pformat(request))
        response = requests.post(self.url, json.dumps(request), timeout=60)
        response.raise_for_status()
        response = json.loads(response.content)
        _logger.info("response received:\n%s", pprint.pformat(response))

        messages = response.get('messages')
        if messages and messages.get('resultCode') == 'Error':
            err_msg = messages.get('message')[0].get('text', '')

            tx_errors = response.get('transactionResponse', {}).get('errors')
            if tx_errors:
                if err_msg:
                    err_msg += '\n'
                err_msg += '\n'.join([e.get('errorText', '') for e in tx_errors])

            return {
                'err_code': messages.get('message')[0].get('code'),
                'err_msg': err_msg,
            }
        return response

    def get_address_info(self, partner):
        return {
            'billTo': {
                'firstName': '' if partner.is_company else partner.firstname,
                'lastName': partner.lastname or partner.name,  # lastName is always required
                'company': partner.name if partner.is_company else partner.parent_id.name,
                'address': '%s %s' % (partner.street or '', partner.street2 or ''),
                'city': partner.city,
                'state': partner.state_id.name or '',
                'zip': partner.zip,
                'country': partner.country_id.name or '',
            }
        }

    def create_customer_profile(self, partner=False):
        """
            Create Authorize net profile
            @param partner: browse record object of res.partner
            return : longint profile id
        """
        if not partner:
            return False

        response = self._make_request('createCustomerProfileRequest', {
            'profile': {
                'merchantCustomerId': partner.customer_code or 'ODOO-%s' % partner.id,
                'email': partner.email or ''
            }
        })
        if not response.get('customerProfileId'):
            _logger.warning('Unable to create customer profile \n {err_code}\n{err_msg}'.format(**response))
        return response

    def create_payment_profile(self, profile_id, partner, opequedata):
        """
            Authorize a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param amount : total amount to authorize
            return : transaction id
        """

        response = self._make_request('createCustomerPaymentProfileRequest', {
            'customerProfileId': profile_id,
            # 'validationMode': 'liveMode' if self.state == 'enabled' else 'testMode',
            'paymentProfile': {
                **self.get_address_info(partner),
                'payment': {**opequedata},
            },
            'validationMode': 'liveMode' if self.state == 'enabled' else 'testMode',
        })
        if not response.get('customerPaymentProfileId'):
            _logger.warning('Unable to create customer profile \n {err_code}\n{err_msg}'.format(**response))
            return response
        return self.get_payment_profile_info(response)

    def get_payment_profile_info(self, payment_response):
        return self._make_request('getCustomerPaymentProfileRequest', {
            "customerProfileId": payment_response.get('customerProfileId'),
            "customerPaymentProfileId": payment_response.get('customerPaymentProfileId'),
            "includeIssuerInfo": "true"
        })
