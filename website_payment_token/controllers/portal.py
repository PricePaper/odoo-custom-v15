# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import datetime
from odoo.http import request
from odoo import tools,_
import logging
_logger = logging.getLogger(__name__)

class PortalRequest(CustomerPortal):


    @http.route(['/my/generate/token'],type='json',auth='user',website=True)
    def generate_new_token(self,**kw):
        _logger.info(f'======================={kw}')
        vals={}
        if kw.get('is_delivery'):
            vals.update(
                is_for_shipping_id = True,
                shipping_id = int(kw.get('partner_shipping_id',0)),
            )
        if kw.get('is_default'):
            vals.update(
                is_default = True
            )
        vals.update(
            address_id = int(kw.get('partner_id',0)),
            exp_month = kw.get('exp_month'),
            card_code = kw.get('card_code'),
            card_no = kw.get('card_no'),
            name = kw.get('name',''),
            exp_year =  kw.get('exp_year'),
            partner_id = request.env.user.partner_id.id,
            profile_id = request.env.user.partner_id.payment_token_ids and request.env.user.partner_id.payment_token_ids[0].authorize_profile or '',
        )

        generate_token_id = request.env['generate.payment.token'].sudo().create(vals)
        generate_token_id.generate_token()
        return True

    @http.route(['/my/payment/token'], type='http', auth="user", website=True)
    def portal_my_token(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id
        payment_token_ids = partner_id.payment_token_ids
        billing_addresses = partner_id.child_ids
        shipping_addresses = partner_id.child_ids.filtered(lambda x: x.type=="delivery")
        values.update(token_ids = payment_token_ids,page_name='payment_token',exp_year = [(str(num), str(num)) for num in range(datetime.now().year, datetime.now().year + 7)],billing=billing_addresses,shipping=shipping_addresses)
        return request.render("website_payment_token.partner_token", values)
    

