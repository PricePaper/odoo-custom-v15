import json
import logging
import pprint
from uuid import uuid4
from odoo.addons.payment import utils as payment_utils
import requests
from odoo.exceptions import ValidationError

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
        self.transaction_key = acquirer.sudo().authorize_transaction_key
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
        # todo remove logger to avoid printing sensitive informations
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
                'phoneNumber': partner.phone or partner.mobile or '',
                'faxNumber': partner.fax_number or ''
            }
        }

    def create_customer_profile(self, partner=False, address=False, shipping_id=False):
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

    def create_customer_profile_with_payment(self, partner=False, address=False, opequedata=False):
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
                "description": partner.display_name[:25] or partner.name[:25],
                'email': partner.email or ''
            }
        })
        if not response.get('customerProfileId'):
            _logger.warning('Unable to create customer profile \n {err_code}\n{err_msg}'.format(**response))
        return response

    def create_payment_profile(self, profile_id, partner, opequedata, address_id=False, shipping_id=False):
        """
            Authorize a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param amount : total amount to authorize
            return : transaction id
        """

        response = self._make_request('createCustomerPaymentProfileRequest', {
            'customerProfileId': profile_id,
            'paymentProfile': {
                "customerType": "business" if partner.is_company else "individual",
                **self.get_address_info(address_id or partner),
                'payment': {**opequedata},
            },
            'validationMode': 'liveMode' if self.state == 'enabled' else 'testMode',
        })
        if not response.get('customerPaymentProfileId'):
            _logger.warning('Unable to create customer profile \n {err_code}\n{err_msg}'.format(**response))
            return response
        return self.get_payment_profile_info(response)

    def create_shipping_profile(self, profile_id, partner):
        response = self._make_request(
            "createCustomerShippingAddressRequest",
            {
                "customerProfileId": profile_id,
                "address": {**self.get_address_info(partner)['billTo']},
                "defaultShippingAddress": False

            })

    def _format_response(self, response, operation):
        if response and response.get('err_code'):
            return {
                'x_response_code': response.get('err_code'),
                'x_response_reason_text': response.get('err_msg')
            }
        else:
            return {
                'x_response_code': response.get('transactionResponse', {}).get('responseCode'),
                'x_trans_id': response.get('transactionResponse', {}).get('transId'),
                'x_type': operation,
            }

    def get_payment_profile_info(self, payment_response):
        return self._make_request('getCustomerPaymentProfileRequest', {
            "customerProfileId": payment_response.get('customerProfileId'),
            "customerPaymentProfileId": payment_response.get('customerPaymentProfileId'),
            "includeIssuerInfo": "true"
        })

    def get_line_item_info(self, order):
        res = []
        for line in order.order_line.filtered(lambda r: not r.is_delivery and not r.is_downpayment)[:30]:
            res.append({

                "itemId": line.product_id.default_code and line.product_id.default_code[:30] or '',
                "name": line.product_id.name and line.product_id.name[:30],
                "description": line.name and line.name[:254] or '',
                "quantity": line.product_uom_qty,
                "unitPrice": line.price_unit,
                "taxable": True if line.tax_id else False,

            })
        return {"lineItem": res}

    def get_invoice_line_item_info(self, invoice):
        res = []
        for line in invoice.invoice_line_ids[:30]:
            res.append({
                "itemId": line.product_id.default_code and line.product_id.default_code[:30] or '',
                "name": line.product_id.name and line.product_id.name[:30],
                "description": line.name and line.name[:254] or '',
                "quantity": line.quantity,
                "unitPrice": line.price_unit,
                "taxable": True if line.tax_ids else False,

            })
        return {"lineItem": res}

    def get_tax_exempt(self, order):
        res = 'false'
        if order.fiscal_position_id.is_tax_exempt:
            res = 'true'
        return res

    def get_tax_info(self, order, from_invoice=False):

        tax_name = ''
        if from_invoice:
            tax_name = ','.join([','.join(line.tax_ids.mapped('name')) for line in order.invoice_line_ids if line.tax_ids])
        else:
            tax_name = ','.join([','.join(line.tax_id.mapped('name')) for line in order.order_line if line.tax_id])
        return {
            "amount": order.amount_tax,
            "name": tax_name and tax_name[:30] or '',
            "description": tax_name and tax_name[:254] or ''
        }

    def get_shipping_info(self, order, from_invoice=False):

        shipping_charge = 0
        carrier_name = ''
        carrier_product_name = ''
        carrier_id = False
        if from_invoice:
            delivery_line = order.invoice_line_ids.sale_line_ids.filtered(lambda rec: rec.is_delivery)
            if delivery_line:
                shipping_charge = sum(delivery_line.mapped('price_subtotal')) or 0
                carrier_id = delivery_line.mapped('order_id')[0].carrier_id
        else:
            shipping_charge = sum(order.order_line.filtered(lambda rec: rec.is_delivery).mapped('price_subtotal')) or 0
            carrier_id = order.carrier_id

        if carrier_id:
            carrier_name = carrier_id.name and order.carrier_id.name[:30]
            if carrier_id.product_id:
                carrier_product_name = carrier_id.product_id.display_name[:254]
        return {
            "amount": shipping_charge,
            "name": carrier_name,
            "description": carrier_product_name
        }

    def check_avs_response(self, response):
        if response and response.get('transactionResponse', False):
            avs_res = response.get('transactionResponse').get('avsResultCode', '')
            if avs_res != 'Y':
                msg = ''
                if avs_res == 'A':
                    msg = 'The street address matched, but the postal code did not.'
                elif avs_res == 'B':
                    msg = 'No address information was provided.'
                elif avs_res == 'E':
                    msg = 'The AVS check returned an error.'
                elif avs_res == 'G':
                    msg = 'The card was issued by a bank outside the U.S. and does not support AVS.'
                elif avs_res == 'N':
                    msg = 'Neither the street address nor postal code matched.'
                elif avs_res == 'P':
                    msg = 'AVS is not applicable for this transaction.'
                elif avs_res == 'R':
                    msg = 'Retry — AVS was unavailable or timed out.'
                elif avs_res == 'S':
                    msg = 'AVS is not supported by card issuer.'
                elif avs_res == 'U':
                    msg = 'Address information is unavailable.'
                elif avs_res == 'W':
                    msg = 'The US ZIP+4 code matches, but the street address does not.'
                elif avs_res == 'X':
                    msg = 'Both the street address and the US ZIP+4 code matched.'
                elif avs_res == 'Z':
                    msg = 'The postal code matched, but the street address did not.'
                if msg:
                    raise ValidationError(msg)

    def authorize_transaction(self, transaction, order, invoice=False):
        """
            Authorize a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param amount : total amount to authorize
            return : transaction id
        """
        response = self._make_request("createTransactionRequest", {
            "refId": transaction.reference,
            "transactionRequest": {
                "transactionType": "authOnlyTransaction",
                "amount": transaction.amount,
                "currencyCode": transaction.currency_id.name,  # TODO
                'profile': {
                    'customerProfileId': transaction.token_id.authorize_profile,
                    'paymentProfile': {
                        'paymentProfileId': transaction.token_id.acquirer_ref,
                    }
                },
                "solution": {  # todo fix this with values from api credentials
                    "id":
                        "AAA100302",
                    "name":
                        "Test Solution #1"
                },
                "terminalNumber": transaction.env.user.id,
                "order": {
                    "invoiceNumber": transaction.reference,
                    "description": order.note or 'description',
                },
                "lineItems": self.get_line_item_info(order),
                "tax": {**self.get_tax_info(order)},
                "duty": {
                    "amount": 0.00,
                    "name": 'no duty',
                    "description": 'no duty'
                },
                "shipping": {**self.get_shipping_info(order)},
                "taxExempt": self.get_tax_exempt(order),
                "poNumber": order.client_order_ref or "Not provided",
                "customer": {
                    "type": "business" if transaction.partner_id.is_company else "individual",
                    "id": transaction.partner_id.customer_code,
                    "email": transaction.partner_id.email,
                },
                # **self.get_address_info(order.partner_invoice_id),

                "shipTo": {
                    **self.get_address_info(order.partner_shipping_id).get('billTo')
                },
                "customerIP": payment_utils.get_customer_ip_address(),
                "retail": {
                    "marketType": 0,
                    "deviceType": 8,
                },
                "employeeId": transaction.env.user.id,
                "authorizationIndicatorType": {
                    "authorizationIndicator": "pre"
                }
            }

        })
        self.check_avs_response(response)
        return self._format_response(response, 'auth_only')



    def authorize_transaction_from_invoice(self, transaction, invoice):
        """
            Authorize a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param amount : total amount to authorize
            return : transaction id
        """
        response = self._make_request("createTransactionRequest", {
            "refId": transaction.reference,
            "transactionRequest": {
                "transactionType": "authOnlyTransaction",
                "amount": transaction.amount,
                "currencyCode": transaction.currency_id.name,  # TODO
                'profile': {
                    'customerProfileId': transaction.token_id.authorize_profile,
                    'paymentProfile': {
                        'paymentProfileId': transaction.token_id.acquirer_ref,
                    }
                },
                "solution": {  # todo fix this with values from api credentials
                    "id":
                        "AAA100302",
                    "name":
                        "Test Solution #1"
                },
                "terminalNumber": transaction.env.user.id,
                "order": {
                    "invoiceNumber": transaction.reference,
                    "description": invoice.note or 'description',
                },
                "lineItems": self.get_invoice_line_item_info(invoice),
                "tax": {**self.get_tax_info(invoice, from_invoice=True)},
                "duty": {
                    "amount": 0.00,
                    "name": 'no duty',
                    "description": 'no duty'
                },
                "shipping": {**self.get_shipping_info(invoice, from_invoice=True)},
                "taxExempt": self.get_tax_exempt(invoice),
                "poNumber": invoice.ref or "Not provided",
                "customer": {
                    "type": "business" if transaction.partner_id.is_company else "individual",
                    "id": transaction.partner_id.customer_code,
                    "email": transaction.partner_id.email,
                },


                "shipTo": {
                    **self.get_address_info(invoice.partner_id).get('billTo')
                },
                "customerIP": payment_utils.get_customer_ip_address(),
                "retail": {
                    "marketType": 0,
                    "deviceType": 8,
                },
                "employeeId": transaction.env.user.id,
                "authorizationIndicatorType": {
                    "authorizationIndicator": "pre"
                }
            }

        })
        self.check_avs_response(response)
        return self._format_response(response, 'auth_only')
