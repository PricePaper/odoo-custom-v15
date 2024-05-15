# -*- coding: utf-8 -*-

from odoo import api, models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    mobile_app_availability = fields.Boolean("Show in mobile app")

    @api.model
    def wrapper_fetch_shipping_methods(self):
        result = []

        shipping_methods = self.search(
            [('mobile_app_availability', '=', True), ('delivery_type', 'in', ['fixed', 'base_on_rule'])])

        if shipping_methods:
            for method in shipping_methods:

                destination_availability = {
                    'countries': method.country_ids.mapped('name'),
                    'states': method.state_ids.mapped('name')
                }

                if method.delivery_type == 'fixed':
                    result.append({'name': method.name,
                                   'delivery_type': method.delivery_type,
                                   'price': method.fixed_price,
                                   'destination_availability': destination_availability
                                   })
                else:
                    rule_list = []
                    for rule in method.price_rule_ids:

                        delivery_cost = {
                            'list_base_price': rule.list_base_price,
                            'operator1': '+',
                            'list_price': rule.list_price,
                            'operator2': '*',
                            'variable_factor': rule.variable_factor,
                            'total_cost': rule.list_base_price if rule.list_price == 0 else None
                        }

                        rule_list.append({
                            'condition': rule.variable,
                            'operator': rule.operator,
                            'maximum_value': rule.max_value,
                            'delivery_cost': delivery_cost
                        })

                    result.append({
                        'name': method.name,
                        'delivery_type': method.delivery_type,
                        'price_rule': rule_list,
                        'destination_availability': destination_availability
                    })

        return result
