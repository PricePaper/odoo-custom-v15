# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class codController(http.Controller):
    _accept_url = '/payment/cod/feedback'

    @http.route(_accept_url, type='http', auth='public', methods=['POST'], csrf=False)
    def cod_form_feedback(self, **post):
        _logger.info("beginning _handle_feedback_data with post data %s", pprint.pformat(post))
        request.env['payment.transaction'].sudo()._handle_feedback_data('cod', post)
        return request.redirect('/payment/status')
