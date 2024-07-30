# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import werkzeug
import itertools
import pytz
import babel.dates
from collections import OrderedDict

from odoo import http, fields
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.http import request
from odoo.osv import expression
from odoo.tools import html2plaintext
from odoo.tools.misc import get_lang
from odoo.tools import sql
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0,product_custom_attribute_values=None, no_variant_attribute_values=None,express=False, **kwargs):
        if not request.env.user._is_public():
            return super(WebsiteSale,self).cart_update(product_id=product_id, add_qty=add_qty, set_qty=set_qty,product_custom_attribute_values=product_custom_attribute_values, no_variant_attribute_values=no_variant_attribute_values,express=express, **kwargs)
        else:
            raise Forbidden()
        
    


class WebsiteBlog(http.Controller):

   

    @http.route('/gen/captcha',type='json', auth="public", website=True,csrf=False)
    def gen_captcha(self,**kw):
        template = request.env['ir.ui.view']._render_template("website_base.captcha_check", {})
        return{
            'status':True,
            'template':template
        }
    @http.route('/contact/crm/lead',type='json', auth="public", website=True,csrf=False)
    def contact_crm(self,**kw):
        crm_vals = {
            'name':'Website Contact Us',
            'contact_name':kw.get('name'),
            'partner_name':kw.get('cname'),
            'email_from':kw.get('email'),
            'phone':kw.get('phone'),
            'street':kw.get('address'),
            'description':kw.get('comments'),
            'type' :'lead'
        }
        crm_id = request.env['crm.lead'].sudo().create(crm_vals)
        if crm_id:
            return {
                'status':True
            }
        else:
            return{
                'status':False
            }