# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import werkzeug
import itertools
import pytz
import babel.dates
from collections import OrderedDict

from odoo import http, fields
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.http import request
from odoo.osv import expression
from odoo.tools import html2plaintext
from odoo.tools.misc import get_lang
from odoo.tools import sql


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
            'description':kw.get('comments')
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
