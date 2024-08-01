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


    def get_authorize_client_key(self):
        acquirer = self.sudo().env['payment.acquirer'].search([('provider', '=', 'authorize')])
        if acquirer:
            return [{'login': acquirer.authorize_login, 'client': acquirer.authorize_client_key}]
        else:
            return False

    def get_mobile_sale_team(self):
        team = self.env['ir.config_parameter'].sudo().get_param('ppt_mobile_apis.mobile_app_sale_team')
        if team:
            return {'team_id': int(team)}
        return {'team_id': False}
