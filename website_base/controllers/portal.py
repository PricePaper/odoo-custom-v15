# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import binascii

from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request

from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.payment import utils as payment_utils
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


# class CustomerPortal(portal.CustomerPortal):
                

#     def _prepare_quotations_domain(self, partner):
#         res = super(CustomerPortal,self)._prepare_quotations_domain(partner)
#         res.append(('payment_term_id','!=',False))
#         return res

#     def _prepare_orders_domain(self, partner):
#         res = super(CustomerPortal,self)._prepare_orders_domain(partner)
#         res.append(('payment_term_id','!=',False))
#         return res
        
