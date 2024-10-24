# -*- coding: utf-8 -*-

from odoo import api, models, fields
from psycopg2 import IntegrityError
from odoo.exceptions import ValidationError



class SaleOrder(models.Model):
    _inherit = "sale.order"

    mapp_record_id = fields.Char('Mapp Unique ID')
    last_updated_on = fields.Datetime(string='Last Updated on')

    @api.model
    def create(self, vals):
        vals['last_updated_on'] = fields.Datetime.now()
        return super(SaleOrder, self).create(vals)

    def write(self, vals):
        val_keys = vals.keys()
        if 'state' in val_keys or 'payment_term_id' in val_keys or \
            'expected_date' in val_keys or 'release_date' in val_keys or \
            'deliver_by' in val_keys or 'partner_shipping_id' in val_keys or  \
            'sales_person_ids' in val_keys or 'token_id' in val_keys:
            vals['last_updated_on'] = fields.Datetime.now()
        return super(SaleOrder, self).write(vals)

    _sql_constraints = [
      ('sale_uniq_mobileuuid', 'unique (mapp_record_id)', 'Sale Order: The Mobile UUID must be Unique !')
      ]

    @api.constrains('mapp_record_id')
    def _check_unique_constrain(self):
        for rec in self:
            if rec.mapp_record_id:
                result = self.sudo().search([('mapp_record_id', '=', self.mapp_record_id), ('id', '!=', self.id)])
                if result:
                    raise ValidationError('Mapp Unique ID unique constrain')

    @api.model
    def sale_order_create_write_wrapper(self, method, vals, record_id=False):
        msg = 'success'
        if method == 'create':
            try:
                new_order = self.create(vals)
                for line in new_order.order_line:
                    line.onchange_get_last_sale_info()
                return {'msg': msg, 'order_id': new_order.id, 'uuid': vals.get('mapp_record_id', '')}
            except IntegrityError as e:
                msg = e.pgerror
            except Exception as e:
                msg = str(e)
            return {'msg': msg, 'uuid': vals.get('mapp_record_id', '')}
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
            try:
                order.write(vals)
                for line in order.order_line:
                    line.onchange_get_last_sale_info()
                return {'msg': msg, 'uuid': vals.get('mapp_record_id', '')}
            except IntegrityError as e:
                msg = e.pgerror
            except Exception as e:
                msg = str(e)
            return {'msg': msg, 'uuid': vals.get('mapp_record_id', '')}
        return {}

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
    last_updated_on = fields.Datetime(string='Last Updated on')

    @api.model
    def create(self, vals):
        vals['last_updated_on'] = fields.Datetime.now()
        return super(SaleOrderLine, self).create(vals)

    def write(self, vals):
        val_keys = vals.keys()
        if 'price_unit' in val_keys or 'order_id' in val_keys or \
           'sequence' in val_keys or 'is_redemption_product' in val_keys or \
           'product_id' in val_keys or 'product_uom_qty' in val_keys:
            vals['last_updated_on'] = fields.Datetime.now()
        return super(SaleOrderLine, self).write(vals)

    _sql_constraints = [
    ('sale_line_uniq_mobileuuid', 'unique (mapp_record_id)', 'Sale Line: The Mobile UUID must be Unique !')
    ]
