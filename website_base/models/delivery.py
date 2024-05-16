# -*- coding: utf-8 -*-

from odoo import api, models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    mobile_app_availability = fields.Boolean("Show in mobile app")

    @api.model
    def wrapper_fetch_shipping_methods(self, partner_id=None):
        """
        Fetches shipping methods based on the boolean mobile_app_availability,and partner_id.
        default key added to identify default shipping method for the partner
        @param partner_id: res.partner id
        @return: list of dictionary with shipping methods
        """
        result = []
        if partner_id and not isinstance(partner_id, int):
            return result

        shipping_methods = self.search(
            [('mobile_app_availability', '=', True), ('delivery_type', 'in', ['fixed', 'base_on_rule'])])

        default_delivery_method = self
        if partner_id:
            # if partner_id is valid and default_deliver_carrier_id present add to fetched shipping_methods
            partner = self.env['res.partner'].browse(partner_id)
            default_delivery_method = partner and partner.property_delivery_carrier_id
            shipping_methods |= default_delivery_method

        if shipping_methods:
            for method in shipping_methods:
                # default: True key passed to identify the delivery method belongs to the partner
                is_default_delivery_method = (method == default_delivery_method)

                destination_availability = {
                    'countries': method.country_ids.mapped('name'),
                    'states': method.state_ids.mapped('name')
                }

                if method.delivery_type == 'fixed':
                    result.append({'name': method.name,
                                   'delivery_type': method.delivery_type,
                                   'price': method.fixed_price,
                                   'destination_availability': destination_availability,
                                   'default': is_default_delivery_method
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
                        'destination_availability': destination_availability,
                        'default': is_default_delivery_method
                    })

        return result
