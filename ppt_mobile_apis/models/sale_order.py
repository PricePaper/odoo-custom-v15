# -*- coding: utf-8 -*-

from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    mapp_record_id = fields.Char('Mapp Unique ID')

    @api.model
    def sale_order_create_write_wrapper(self, method, vals, record_id=False):
        if method == 'create':
            order = self.search([('mapp_record_id', '=', vals.get('mapp_record_id', ''))])
            if order:
                return True
            else:
                new_order = self.create(vals)
                return new_order.id
        elif method == 'write':
            order = self.search([('id', '=', record_id)])
            if not order:
                return True
            for line in vals.get('order_line', []):
                if line[0] == 0:
                    if line[2].get('mapp_record_id', False):
                        order_line = order.order_line.filtered(lambda r: r.mapp_record_id == line[2].get('mapp_record_id', False))
                        if order_line:
                            line[0] = 1
                            line[1] = order_line.id
            return order.write(vals)
        return True

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

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    mapp_record_id = fields.Char('Mapp Unique ID')
