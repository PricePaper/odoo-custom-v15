# -*- coding: utf-8 -*-

from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def wrapper_sale_order_action_confirm(self):
        self.ensure_one()
        result = []

        message = {'success': False,
                   'error': False}

        res = self.sudo().action_confirm()

        if isinstance(res, dict):
            message['error'] = res.get('context', {}).get('default_warning_message', 'No warning message provided')
        elif res:
            message['success'] = True

        result.append(message)
        return result
