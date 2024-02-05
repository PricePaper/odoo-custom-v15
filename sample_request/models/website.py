# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = "website"


    def get_sample_oder(self,force_create=True):

        self.ensure_one()
        partner = self.env.user.partner_id
        sample_request_id = request.session.get('sample_request_id')
        sample_request = self.env['sample.request']
        if not self.env.user._is_public():
            sample_request = sample_request.sudo().search([('partner_id','=',partner.id),('state','=','draft')])
        elif sample_request_id:
            sample_request = sample_request.sudo().browse([int(sample_request_id)])
        if force_create and not sample_request:
            sr_data = {
                'partner_id':partner.id if not self.env.user._is_public() else False,
                'state':'draft'
            }
            sample_request = sample_request.sudo().create(sr_data)

        request.session['sample_request_id'] = sample_request.id if sample_request else False
        return sample_request
