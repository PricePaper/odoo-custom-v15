from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError
from ..authorize_request_custom import AuthorizeAPICustom


class PaymentTokenize(models.TransientModel):
    _name = "generate.payment.token"

    @api.model
    def _get_profile_id(self):
        partner = self._get_partner_id()
        if partner:
            partner = self.env['res.partner'].browse(partner)
            return partner.payment_token_ids and partner.payment_token_ids[0].authorize_profile or ''
        return ''

    @api.model
    def _get_partner_id(self):
        if self._context.get('partner_id') or self.env.context.get('active_model') == 'res.partner' and self.env.context.get('active_id'):
            partner = self.env['res.partner'].browse(self._context.get('partner_id', self.env.context.get('active_id')))
            return partner.id
        return False

    @api.model
    def _get_authorize_acquirer(self):
        return self.env['payment.acquirer'].search([('provider', '=', 'authorize')], limit=1).id

    acquirer_id = fields.Many2one('payment.acquirer', "Acquirer Account", default=_get_authorize_acquirer, required=True)
    name = fields.Char('Card holder name')
    card_no = fields.Char('Credit Card Number', size=16)
    card_code = fields.Char('CVV',size=4)
    exp_month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
         ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Card Expiration Month')

    exp_year = fields.Selection([(str(num), str(num)) for num in range(datetime.now().year, datetime.now().year + 7)], 'Card Expiration Year')
    partner_id = fields.Many2one('res.partner', "Partner", default=_get_partner_id)
    profile_id = fields.Char('Profile ID', default=_get_profile_id)
    is_for_shipping_id = fields.Boolean("Is for delivery address?")
    shipping_id = fields.Many2one('res.partner', "Delivery address")
    address_id = fields.Many2one('res.partner', "Billing address", required=True)
    is_default = fields.Boolean('Is Default Token?')

    def generate_token(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError("Internal Error please contact your system administrator")
        authorize_api = AuthorizeAPICustom(self.acquirer_id)
        if not self.profile_id:
            profile = authorize_api.create_customer_profile(self.partner_id, self.address_id, self.shipping_id)
            if not profile.get('customerProfileId'):
                raise UserError("Profile creation error\n{err_code}\n{err_msg}".format(**profile))
            self.profile_id = profile.get('customerProfileId')
        opequedata = {
            'creditCard': {
                'cardNumber': self.card_no,
                'expirationDate': '%s-%s' % (self.exp_year, self.exp_month),
                'cardCode': self.card_code,
            }
        }
        token = authorize_api.create_payment_profile(self.profile_id, self.partner_id, opequedata, self.address_id, self.shipping_id)
        if not token.get('paymentProfile', {}).get('customerPaymentProfileId'):
            raise UserError("Token creation error\n{err_code}\n{err_msg}".format(**token))
        # shipping  = authorize_api.create_shipping_profile(self.profile_id, self.partner_id)
        self.env['payment.token'].create({
            'acquirer_id': self.acquirer_id.id,
            'name': "%s - %s - %s" % (self.partner_id.name,
                                      token.get('paymentProfile', {}).get('payment', {}).get('creditCard', {}).get('cardType'),
                                      token.get('paymentProfile', {}).get('payment', {}).get('creditCard', {}).get('cardNumber').replace('X', '')),
            'partner_id': self.partner_id.id,
            'acquirer_ref': token.get('paymentProfile', {}).get('customerPaymentProfileId'),
            'authorize_profile': self.profile_id,
            'authorize_payment_method_type': self.acquirer_id.authorize_payment_method_type,
            'verified': True,
            'shipping_id': self.shipping_id.id,
            'address_id': self.address_id.id,
            'is_default': self.is_default
        })
        self.write({
            'card_no': 'null',
            'exp_year': '',
            'exp_month': '',
            'card_code': '',
        })
        return True


PaymentTokenize()
