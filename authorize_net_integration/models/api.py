# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from xml.dom.minidom import parseString
import requests
import re
import xml.etree.ElementTree as ET


class AuthorizenetApi(models.Model):
    TEST_URL = 'https://apitest.authorize.net/xml/v1/request.api'
    PRODUCTION_URL = 'https://api2.authorize.net/xml/v1/request.api'

    _name = 'authorizenet.api'
    _description = 'Configuration for Authorize.Net payment gateway'

    name = fields.Char('Name', required=True)
    api_login = fields.Char('Api Login', required=True)
    transactionkey = fields.Char('Transaction Key', required=True)
    environment = fields.Selection(
        [('livemode', 'Live mode'), ('testmode_server', 'Test mode (in production server)'), ('testmode', 'Test mode')],
        'Environment', required=True, default='testmode')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    sequence = fields.Integer("Sequence", default=100)

    @api.model
    def _get_credentials(self, company_id=None):
        """
           returns the configuration for authorize.net payment geteway
           :return type: Tuple of login credentials and url
        """

        domain = [('active', '=', True)]
        if company_id:
            domain.append(('company_id', '=', company_id.id))
        config_id = self.search(domain, limit=1, order="sequence")

        if config_id and config_id.id:
            return config_id.api_login, config_id.transactionkey
        raise UserError(
            'Authorize.Net is not configured \n you can configure in menu Accounting => Configuration => Authorize.Net')

    @api.model
    def _get_url(self, company_id=None):
        """
           returns the authorize.net payment geteway url
           :return type: String authorize.net url
        """
        domain = [('active', '=', True)]
        if company_id:
            domain.append(('company_id', '=', company_id.id))
        config = self.search(domain, limit=1, order="sequence")
        if len(config):
            return self.TEST_URL if config.environment == 'testmode' else self.PRODUCTION_URL
        return False

    @api.model
    def _get_auth_header(self):
        company_id = self.env['res.company']._company_default_get('authorizenet.api')
        login, key = self._get_credentials(company_id=company_id)
        header = """<merchantAuthentication>
                        <name>%s</name>
                        <transactionKey>%s</transactionKey>
                    </merchantAuthentication>""" % (login, key)
        return header

    @api.model
    def _get_error_message(self, response):
        """
        Returns the error code and message
           @param response: request.content 
           @return tuple containing error code and error message
        """
        code, text = False, False
        try:
            response = response.encode('utf-8')
        except:
            response = response
        try:
            res = parseString(response)
            code = res.getElementsByTagName('code')
            code = code and code[0].firstChild.nodeValue
            text = res.getElementsByTagName('text')
            text = text and text[0].firstChild.nodeValue
        except Exception as ex:
            raise UserError('Authorize.Net Warning- XML parse error')
        return code, text

    def _get_status(self, response):
        """
        This method will check the response of authorize.Net and return true if it is success
           @param response: request.content 
           @return Boolean
        """
        res = ''
        try:
            response = response.encode('utf-8')
        except:
            response = response
        try:
            res = parseString(response)
            res = res.getElementsByTagName('resultCode')
            res = res and res[0].firstChild.nodeValue
            if res == 'Error':
                return False
        except Exception as ex:
            raise UserError('Authorize.Net Warning%s' % ex)
        return True

    def _get_transaction_id(self, response):
        """
        return transaction_id
           @param response: request.content 
           @return long int
        """
        try:
            response = response.encode('utf-8')
        except:
            response = response
        try:
            res = parseString(response).getElementsByTagName('directResponse')
            res = res and res[0] and res[0].firstChild.nodeValue or ''
            res = res.split(',')
            return res and res[6] or False
        except Exception as ex:
            raise UserError('Authorize.Net Warning%s' % ex)
        return False

    @api.model
    def _get_profile_id(self, response):
        try:
            response = response.encode('utf-8')

        except:
            response = response
        try:
            res = parseString(response).getElementsByTagName('customerProfileId')
            res = res and res[0] and res[0].firstChild.nodeValue or ''
            return res or False
        except Exception as ex:
            raise UserError('Authorize.Net Warning%s' % ex)
        return False

    def _get_payment_id(self, response):
        """
        return payment_id
           @param response: request.content 
           @return long int
        """
        try:
            response = response.encode('utf-8')
        except:
            response = response
        try:
            res = parseString(response).getElementsByTagName('customerPaymentProfileId')
            res = res and res[0] and res[0].firstChild.nodeValue or ''
            return res or False
        except Exception as ex:
            raise UserError('Authorize.Net Warning%s' % ex)
        return False

    def _get_payment_ids(self, response):
        """
           Get all payment ids
           @param response: request.content list of payment profiles           
           @return list of tuples 
        """

        res = []
        if not response:
            return res
        try:
            response = response.encode('utf-8')
        except:
            response = response
        try:
            response = parseString(response).getElementsByTagName('paymentProfiles')
            for item in response:
                card = item.getElementsByTagName('cardNumber')
                card = card and card[0].firstChild.nodeValue or ''
                payment_id = item.getElementsByTagName('customerPaymentProfileId')
                payment_id = payment_id and payment_id[0].firstChild.nodeValue or ''
                res.append((payment_id, card))
        except Exception as ex:
            raise UserError('Authorize.Net Warning%s' % ex)
        return res

    def _get_payment_id_of_card_no(self, response, card_number):
        """
        return payment_id
           @param response: request.content list of payment profiles
           @param card_number: int card no
           @return long int
        """
        if not card_number:
            return False
        try:
            response = response.encode('utf-8')
        except:
            response = response
        try:
            res = parseString(response).getElementsByTagName('paymentProfiles')
            for item in res:
                card = item.getElementsByTagName('cardNumber')
                card = card and card[0].firstChild.nodeValue or ''
                if card_number[-4:] == card[-4:]:
                    payment_id = item.getElementsByTagName('customerPaymentProfileId')
                    return payment_id and payment_id[0].firstChild.nodeValue or ''
            return False
        except Exception as ex:
            raise UserError('Authorize.Net Warning%s' % ex)
        return False

    @api.model
    def create_authorizenet_profile(self, partner):
        """
            Create Authorize net profile
            @param partner: browse record object of res.partner
            return : longint profile id
        """
        if not partner:
            return False
        auth_header = self._get_auth_header()
        company_id = self.env['res.company']._company_default_get('authorizenet.api')
        url = self._get_url(company_id=company_id)
        cust_id = 'erp-%s' % (partner.id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
            <createCustomerProfileRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                %s                  
                <profile>
                    <merchantCustomerId>%s</merchantCustomerId>
                    <email>%s</email>                                    
                </profile>
            </createCustomerProfileRequest>
            """ % (auth_header, cust_id, partner.email)

        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})

        if not success:
            raise UserError('Authorize.Net Warning - %s\n%s' % self._get_error_message(response))
        profile_id = self._get_profile_id(response)
        partner.write({'profile_id': profile_id})
        return profile_id

    @api.model
    def _get_profile(self, profile_id):
        if not profile_id:
            return False
        auth_header = self._get_auth_header()
        company_id = self.env['res.company']._company_default_get('authorizenet.api')
        url = self._get_url(company_id=company_id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
            <getCustomerProfileRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                %s
                <customerProfileId>%s</customerProfileId>
            </getCustomerProfileRequest>""" % (auth_header, profile_id)

        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})

        if not success:
            raise UserError('Authorize.Net Warning - %s\n%s' % self._get_error_message(response))
        return response

    def check_string(self, inp_string):
        op_string = ''
        if inp_string:
            op_string = inp_string.replace('&', 'and')  # replaces '&' with 'and'
            op_string = re.sub('<.+?>', '', op_string)  # removes any characters in between '<' and '>'
            op_string = re.sub('@.+', '', op_string)  # removes any character that comes after '@'
            op_string = re.sub('[^-,_A-Za-z0-9]', '', op_string)  # repaced all the special character except ,-_  
        return op_string

    @api.model
    def create_payment_profile(self, profile_id, partner, card_no, cvv, expiry_date):
        """
            Authorize a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param amount : total amount to authorize
            return : transaction id
        """
        auth_header = self._get_auth_header()
        company_id = self.env['res.company']._company_default_get('authorizenet.api')
        url = self._get_url(company_id=company_id)
        company = partner.parent_id and partner.parent_id.name or ''
        company = self.check_string(company)
        address = '%s %s' % (partner.street or '', partner.street2 or '')
        address = self.check_string(address)
        state = partner.state_id and partner.state_id.name or ''
        country = partner.country_id and partner.country_id.name or ''
        partner_name = self.check_string(partner.name)
        mode = 'liveMode' if url == self.PRODUCTION_URL else 'testMode'
        auth_data = """<?xml version="1.0" encoding="utf-8"?> 
            <createCustomerPaymentProfileRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">           
                %s    
                <customerProfileId>%s</customerProfileId>  
                <paymentProfile>
                    <billTo>
                        <firstName>%s</firstName>                        
                        <company>%s</company>
                        <address>%s</address>
                        <city>%s</city>
                        <state>%s</state>
                        <zip>%s</zip>
                        <country>%s</country>
                        <phoneNumber>%s</phoneNumber>

                    </billTo>
                    <payment>
                        <creditCard>
                            <cardNumber>%s</cardNumber>
                            <expirationDate>%s</expirationDate>
                            <cardCode>%s</cardCode>
                        </creditCard>
                    </payment>
                </paymentProfile>     
                <validationMode>%s</validationMode>                           
            </createCustomerPaymentProfileRequest>
            """ % (
            auth_header, profile_id, partner_name, company, address, self.check_string(partner.city), state or '',
            partner.zip or '', country or '', partner.phone or '',
            card_no, expiry_date, cvv, mode)
        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})
        if not success:
            code, message = self._get_error_message(response)
            # duplicate payment profile exist
            if code == "E00039":
                res = self._get_profile(profile_id)
                # get existing payment profile id of this card no
                payment_id = self._get_payment_id_of_card_no(res, card_no)
            elif code or message:
                raise UserError('Authorize.Net Warning - %s\n%s' % (code, message))
        else:
            payment_id = self._get_payment_id(response)
        return payment_id

    @api.model
    def authorize_payment(self, profile_id, payment_id, amount, invoice):
        """
            Authorize a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param amount : total amount to authorize
            return : transaction id
        """
        auth_header = self._get_auth_header()
        company_id = self.env['res.company']._company_default_get('authorizenet.api')
        url = self._get_url(company_id=company_id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
                <createCustomerProfileTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                    %s
                    <transaction>
                        <profileTransAuthOnly>
                            <amount>%s</amount>
                            <customerProfileId>%s</customerProfileId>
                            <customerPaymentProfileId>%s</customerPaymentProfileId>
                            <order>
                                <invoiceNumber>%s</invoiceNumber>
                            </order>
                        </profileTransAuthOnly>
                    </transaction>
                </createCustomerProfileTransactionRequest>
                """ % (auth_header, amount, profile_id, payment_id, invoice)

        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})
        if not success:
            raise UserError('Authorize.Net Warning-%s\n%s' % self._get_error_message(response))

        return self._get_transaction_id(response)

    @api.model
    def void_payment(self, profile_id, payment_id, transaction_id):
        """
            Void a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param transaction_id : authorize.net customer transaction_id 
            return : transaction id
        """
        auth_header = self._get_auth_header()
        company_id = self.env['res.company']._company_default_get('authorizenet.api')
        url = self._get_url(company_id=company_id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
                <createCustomerProfileTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                    %s
                    <transaction>
                        <profileTransVoid>
                            <customerProfileId>%s</customerProfileId>
                            <customerPaymentProfileId>%s</customerPaymentProfileId>
                            <transId>%s</transId>
                        </profileTransVoid>
                    </transaction>
                </createCustomerProfileTransactionRequest>
                """ % (auth_header, profile_id, payment_id, transaction_id)

        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})
        if not success:
            code, msg = self._get_error_message_aim(response)
            return False, code, msg
            # raise UserError(_('Authorize.Net Warning'), _('%s\n%s'% self._get_error_message(response)))

        return success, "True", "True"

    @api.model
    def capture_payment(self, profile_id, payment_id, transaction_id, amount):
        """
            Capture a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param transaction_id : authorize.net customer transaction_id            
            @param amount : total amount to authorize
            return : transaction id
        """
        auth_header = self._get_auth_header()
        company_id = self.env['res.company']._company_default_get('authorizenet.api')
        url = self._get_url(company_id=company_id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
            <createCustomerProfileTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                %s
            <transaction>
                <profileTransPriorAuthCapture>
                    <amount>%s</amount>
                    <customerProfileId>%s</customerProfileId>
                    <customerPaymentProfileId>%s</customerPaymentProfileId>
                    <transId>%s</transId>
                </profileTransPriorAuthCapture>
            </transaction>
            </createCustomerProfileTransactionRequest>
            """ % (auth_header, amount, profile_id, payment_id, transaction_id)

        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})
        if not success:
            raise UserError('Authorize.Net Warning-%s\n%s' % self._get_error_message(response))

        return success

    @api.model
    def refund_payment(self, profile_id, payment_id, transaction_id, amount, invoice):
        """
            Refund a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param transaction_id : authorize.net customer payment_id
            @param amount : total amount to authorize
            return : transaction id
        """
        auth_header = self._get_auth_header()
        company_id = self.env['res.company']._company_default_get('authorizenet.api')
        url = self._get_url(company_id=company_id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
                <createCustomerProfileTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                %s
                <transaction>
                    <profileTransRefund>
                        <amount>%s</amount>
                        <customerProfileId>%s</customerProfileId>
                        <customerPaymentProfileId>%s</customerPaymentProfileId>
                        <order>
                            <invoiceNumber>%s</invoiceNumber>

                        </order>
                        <transId>%s</transId>
                    </profileTransRefund>
                </transaction>
            </createCustomerProfileTransactionRequest>
            """ % (auth_header, amount, profile_id, payment_id, invoice, transaction_id)

        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})
        if not success:
            return False
            # raise UserError('Authorize.Net Warning-%s\n%s'% self._get_error_message(response))

        return self._get_transaction_id(response)

    @api.model
    def refund_payment_aim(self, transaction_id, amount, invoice):
        """
            Refund a transaction
            @param profile_id : authorize.net customer profile_id
            @param payment_id : authorize.net customer payment_id
            @param transaction_id : authorize.net customer payment_id
            @param amount : total amount to authorize
            return : transaction id
        """

        auth_header = self._get_auth_header()
        url = self._get_url(company_id=self.company_id)
        auth_datas = """<?xml version="1.0" encoding="utf-8"?>
                            <getTransactionDetailsRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                            %s
                                <transId>%s</transId>
                            </getTransactionDetailsRequest>
                        """ % (auth_header, transaction_id)
        success, response, header, code = self.execute_request(auth_datas, url=url,
                                                               headers={'Content-Type': 'text/xml'})
        res = parseString(response).getElementsByTagName('cardNumber')
        if res:
            card = res[0].firstChild.nodeValue
            expiry = parseString(response).getElementsByTagName('expirationDate')
            # invoice = parseString(response).getElementsByTagName('invoiceNumber')
            # invoice = invoice[0].firstChild.nodeValue
            expiry = expiry[0].firstChild.nodeValue
            auth_data = """<?xml version="1.0" encoding="utf-8"?>
                            <createTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                                %s
                                <refId>123456</refId>
                                <transactionRequest>
                                    <transactionType>refundTransaction</transactionType>
                                    <amount>%s</amount>
                                    <payment>
                                        <creditCard>
                                            <cardNumber>%s</cardNumber>
                                            <expirationDate>%s</expirationDate>
                                        </creditCard>
                                    </payment>
                                     <refTransId>%s</refTransId>
                                     <order>
                                        <invoiceNumber>%s</invoiceNumber>
                                    </order>
                                </transactionRequest>
                            </createTransactionRequest>
                         """ % (auth_header, amount, card, expiry, transaction_id, invoice)
            success, response, header, code = self.execute_request(auth_data, url=url,
                                                                   headers={'Content-Type': 'text/xml'})
            if not success:
                return False
                # raise UserError('Authorize.Net Warning-%s\n%s' % self._get_error_message(response))
            return self._get_transaction_id_aim(response)
        else:
            account_num = parseString(response).getElementsByTagName('accountNumber')
            if not account_num:
                raise UserError('Authorize.Net Warning- No response (may be an eCheck.net transaction')
            account = account_num[0].firstChild.nodeValue
            routingNumber = parseString(response).getElementsByTagName('routingNumber')
            routingNumber = routingNumber[0].firstChild.nodeValue
            nameOnAccount = parseString(response).getElementsByTagName('nameOnAccount')
            nameOnAccount = nameOnAccount[0].firstChild.nodeValue
            transId = parseString(response).getElementsByTagName('transId')
            transId = transId[0].firstChild.nodeValue
            data = """<?xml version="1.0" encoding="UTF-8"?>
            <createTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
               %s
               <refId>12345f6</refId>
               <transactionRequest>
                  <transactionType>refundTransaction</transactionType>
                  <amount>%s</amount>
                  <payment>
                     <bankAccount>
                        <accountType>savings</accountType>
                        <routingNumber>%s</routingNumber>
                        <accountNumber>%s</accountNumber>
                        <nameOnAccount>%s</nameOnAccount>
                        <bankName>US</bankName>
                     </bankAccount>
                  </payment>
                  <refTransId>%s</refTransId>
               </transactionRequest>
            </createTransactionRequest>""" % (auth_header, amount, routingNumber, account, nameOnAccount, transId)
            success, response, header, code = self.execute_request(data, url=url,
                                                                   headers={'Content-Type': 'text/xml'})
            if not success:
                return False
                # raise UserError('Authorize.Net Warning-%s\n%s' % self._get_error_message(response))
            return self._get_transaction_id_aim(response)

    @api.model
    def execute_request(self, content, url='', method='POST', headers={}):
        """
        Communicate with authorize.net api
           @param content: xml string
           @param url: authorize.net url 
           @param method: POST, GET..etc
           @param headers: content header for the api call
           @return tuple containing (status, content, header, status_code)
        """
        if not url:
            company_id = self.env['res.company']._company_default_get('authorizenet.api')
            url = self._get_url(company_id=company_id)
        if not url or 'authorize.net' not in url:
            raise UserError('Authorize.net URL - your authorize.net url is incorrect')
        # TODO add condition to check method
        res = requests.post(url, data=content, headers=headers)
        return self._get_status(res.content), res.content, res.headers, res.status_code

    @api.model
    def authorize_capture_transaction_aim(self, amount, card, cvv, expiry, invoice):
        """
            authorizes and captures transaction in authroze aim(no customer profile)
            @param amount : total amount to authorize
            @param card : credit card number
            @param expiry : credit card expiry
            @param cvv : credit card cvv
            @param order : order reference
            return : transaction id
        """
        print('content', amount, card, cvv, expiry, invoice)
        customer_details = self.env['account.invoice'].search([('id', '=', int(invoice))])
        id = customer_details and customer_details.id
        first_name = self.check_string(
            customer_details and customer_details.partner_id and customer_details.partner_id.name)
        street = False
        city = False
        country = False
        state = False
        zip = False
        email = False
        if customer_details and customer_details.commercial_partner_id:
            street = self.check_string(customer_details.commercial_partner_id.street)
            city = self.check_string(customer_details.commercial_partner_id.city)
            country = customer_details.commercial_partner_id.country_id and customer_details.commercial_partner_id.country_id.name
            state = customer_details.commercial_partner_id.state_id and customer_details.commercial_partner_id.state_id.name
            zip = customer_details.commercial_partner_id.zip
            email = customer_details.partner_id.email
            email = email and email.split(',')
            email = email and str(email[0])
        auth_header = self._get_auth_header()
        url = self._get_url(company_id=self.company_id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
                    <createTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                        %s
                        <transactionRequest>
                            <transactionType>authCaptureTransaction</transactionType>
                            <amount>%s</amount>
                            <payment>
                              <creditCard>
                                <cardNumber>%s</cardNumber>
                                <expirationDate>%s</expirationDate>
                                <cardCode>%s</cardCode>
                              </creditCard>
                            </payment>
                            <order>
                             <invoiceNumber>%s</invoiceNumber>
                            </order>
                            <customer>
                                <id>%s</id>
                                <email>%s</email>
                            </customer>
                             <billTo>
                                  <firstName>%s</firstName>
                                  <address>%s</address>
                                  <city>%s</city>
                                  <state>%s</state>
                                  <zip>%s</zip>
                                  <country>%s</country>

                            </billTo>
                             <retail>
                                <marketType>2</marketType>
                                <deviceType>8</deviceType>
                            </retail>
                        </transactionRequest>
                    </createTransactionRequest>
                    """ % (
            auth_header, round(float(amount), 2), card, expiry, cvv, customer_details.number, id, email, first_name,
            street,
            city, state, zip, country)
        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})
        response_code = response and parseString(response)
        response_code_val = response_code and response_code.getElementsByTagName('responseCode')
        res_code = response_code_val and response_code_val[0].firstChild.nodeValue
        if not res_code:
            return False, "- Something Went Wrong..!!"
        if res_code and int(res_code) != 1 and not success:
            try:
                raise UserError('%s-%s' % self._get_error_message_aim(response))
            except UserError as e:
                return False, e
        if res_code and int(res_code) != 1:
            try:
                raise UserError('%s-%s' % self._get_error_message_aim(response))
            except UserError as e:
                if not e:
                    e = "error"
                return False, e
        print('response', response)
        return self._get_transaction_id_aim(response), False

    @api.model
    def authorize_capture_cheque_transaction_aim(self, amount, invoice, account_name, routing_number, account_number,
                                                 bank_name, eCheque_type, account_type):
        """
            authorizes and captures transaction in authroze aim(e cheque)
            @param amount : total amount to authorize
            @param card : credit card number
            @param expiry : credit card expiry
            @param cvv : credit card cvv
            @param order : order reference
            return : transaction id
        """

        invoice_details = self.env['account.invoice'].search([('id', '=', int(invoice))])
        id = invoice_details and invoice_details.id
        first_name = self.check_string(
            invoice_details and invoice_details.partner_id and invoice_details.partner_id.name)
        street = False
        city = False
        country = False
        state = False
        zip = False
        email = False
        if invoice_details and invoice_details.commercial_partner_id:
            street = self.check_string(invoice_details.commercial_partner_id.street)
            city = self.check_string(invoice_details.commercial_partner_id.city)
            country = invoice_details.commercial_partner_id.country_id and invoice_details.commercial_partner_id.country_id.name
            state = invoice_details.commercial_partner_id.state_id and invoice_details.commercial_partner_id.state_id.name
            zip_code = invoice_details.commercial_partner_id.zip
            email = invoice_details.partner_id.email
            email = email and email.split(',')
            email = email and str(email[0])
        auth_header = self._get_auth_header()
        url = self._get_url(company_id=self.company_id)
        auth_data = """<?xml version="1.0" encoding="UTF-8"?>
                        <createTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                           %s
                           <transactionRequest>
                              <transactionType>authCaptureTransaction</transactionType>
                              <amount>%s</amount>
                              <payment>
                                 <bankAccount>
                                    <accountType>%s</accountType>
                                    <routingNumber>%s</routingNumber>
                                    <accountNumber>%s</accountNumber>
                                    <nameOnAccount>%s</nameOnAccount>
                                    <echeckType>%s</echeckType>
                                    <bankName>%s</bankName>
                                 </bankAccount>
                              </payment>
                              <order>
                                 <invoiceNumber>%s</invoiceNumber>
                                 <description>%s</description>
                              </order>
                              <lineItems>
                                 <lineItem>
                                    <itemId>%s</itemId>
                                    <name>%s</name>
                                    <description>Heres the first line item</description>
                                    <quantity>1.0</quantity>
                                    <unitPrice>%s</unitPrice>
                                 </lineItem>
                              </lineItems>
                              <customer>
                                 <type>individual</type>
                                 <id>%s</id>
                                 <email>shibi.thambi@confianzit.biz</email>
                              </customer>
                              <billTo>
                                 <firstName>%s</firstName>
                                 <lastName>%s</lastName>
                                 <company>%s</company>
                                 <address>%s</address>
                                 <city>%s</city>
                                 <state>%s</state>
                                 <zip>%s</zip>
                                 <country>%s</country>
                              </billTo>
                              <transactionSettings>
                                 <setting>
                                    <settingName>duplicateWindow</settingName>
                                    <settingValue>60</settingValue>
                                 </setting>
                                  <setting>
                                    <settingName>emailCustomer</settingName>
                                    <settingValue>1</settingValue>
                                 </setting>
                              </transactionSettings>
                           </transactionRequest>
                        </createTransactionRequest>""" % (
            auth_header, round(float(amount), 2), account_type, routing_number, account_number, account_name,
            eCheque_type, bank_name, invoice_details.number, invoice_details.number,
            id, invoice_details.number, round(float(amount), 2), invoice_details.partner_id.id, first_name, first_name,
            first_name, first_name, city, state, zip_code, country)
        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})
        response_code = response and parseString(response)
        response_code_val = response_code and response_code.getElementsByTagName('responseCode')
        res_code = response_code_val and response_code_val[0].firstChild.nodeValue
        if not res_code:
            return False, "- Something Went Wrong..!!"
        if res_code and int(res_code) != 1 and not success:
            try:
                raise UserError('%s-%s' % self._get_error_message_aim(response))
            except UserError as e:
                return False, e
        if res_code and int(res_code) != 1:
            try:
                raise UserError('%s-%s' % self._get_error_message_aim(response))
            except UserError as e:
                if not e:
                    e = "error"
                return False, e
        return self._get_transaction_id_aim(response), False

    @api.model
    def _get_error_message_aim(self, response):
        """
        Returns the error code and message
        @param response: request.content
        @return tuple containing error code and error message
        """
        code, errorText = False, False
        try:
            response = response.encode('utf-8')
        except:
            response = response
        try:
            res = parseString(response)
            code = res.getElementsByTagName('code')
            code = code and code[0].firstChild.nodeValue
            errorText = res.getElementsByTagName('errorText')
            if not errorText:
                errorText = res.getElementsByTagName('text')
            errorText = errorText and errorText[0].firstChild.nodeValue
        except Exception as ex:
            raise UserError('Authorize.Net Warning - XML parse error')
        return code, errorText

    def _get_transaction_id_aim(self, response):
        """
        return transaction_id
           @param response: request.content
           @return long int
        """
        try:
            response = response.encode('utf-8')
        except:
            response = response
        try:
            res = parseString(response).getElementsByTagName('transactionResponse')
            res = res[0].getElementsByTagName('transId')[0].firstChild.nodeValue
            return res or False
        except Exception as ex:
            raise UserError('Authorize.Net Warning-%s' % ex)
        return False

    @api.model
    def void_transaction_aim(self, transaction_id):
        """
            voids a pendingcapture transaction in authroze aim(no customer profile)
            @param
1-80 / 202
￼￼
 transaction_id : id of transaction to void
            return : status
        """

        auth_header = self._get_auth_header()
        url = self._get_url(company_id=self.company_id)
        auth_data = """<?xml version="1.0" encoding="utf-8"?>
                    <createTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
                        %s
                        <transactionRequest>
                            <transactionType>voidTransaction</transactionType>
                            <refTransId>%s</refTransId>
                        </transactionRequest>
                    </createTransactionRequest>
                    """ % (auth_header, transaction_id)
        success, response, header, code = self.execute_request(auth_data, url=url, headers={'Content-Type': 'text/xml'})
        if not success:
            code, msg = self._get_error_message_aim(response)
            return False, code, msg
            # raise UserError('Authorize.Net Warning%s\n%s'% self._get_error_message_aim(response))
        return success, "True", "True"


AuthorizenetApi()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
