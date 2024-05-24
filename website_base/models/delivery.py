# -*- coding: utf-8 -*-

from odoo import api, models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    mobile_app_availability = fields.Boolean("Show in Mobile App")
    is_store_pickup = fields.Boolean("Enable Store Pickup")

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
                                   'delivery_carrier_id': method.id,
                                   'price': method.fixed_price,
                                   'destination_availability': destination_availability,
                                   'is_store_pickup': method.is_store_pickup,
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
                        'delivery_carrier_id': method.id,
                        'delivery_type': method.delivery_type,
                        'price_rule': rule_list,
                        'destination_availability': destination_availability,
                        'is_store_pickup': method.is_store_pickup,
                        'default': is_default_delivery_method
                    })

        return result

    # @api.model
    # def wrapper_add_update_shipping_cost(self, kwargs=None):
    #     if kwargs is None:
    #         kwargs = {}
    #
    #     order_id = kwargs.get('order_id', False)
    #     carrier_id = kwargs.get('carrier_id', False)
    #
    #     result = []
    #     result_dict = {'success': False, 'delivery_message': False, 'delivery_price': 0, 'display_price': 0,
    #                    'error': False}
    #
    #     if not isinstance(order_id, int) or not isinstance(carrier_id, int):
    #         result_dict['error'] = 'Invalid order_id or carrier_id'
    #         result.append(result_dict)
    #         return result
    #
    #     order_id = self.env['sale.order'].browse(order_id)
    #     carrier_id = self.env['delivery.carrier'].browse(carrier_id)
    #
    #     if not order_id.exists() or not carrier_id.exists():
    #         result_dict['error'] = 'Order or Carrier does not exist'
    #         result.append(result_dict)
    #         return result
    #
    #     if carrier_id.delivery_type in ('fixed', 'base_on_rule'):
    #         vals = carrier_id.rate_shipment(order_id)
    #         if vals.get('success'):
    #             result_dict.update({
    #                 'success': True,
    #                 'delivery_message': vals.get('warning_message', False),
    #                 'delivery_price': vals['price'],
    #                 'display_price': vals['carrier_price'],
    #                 'error': False
    #             })
    #             order_id.set_delivery_line(carrier_id, vals['price'])
    #             order_id.write({
    #                 'recompute_delivery_price': False,
    #                 'delivery_message': vals.get('warning_message', False),
    #             })
    #         else:
    #             result_dict.update({
    #                 'error': vals.get('error_message', vals['error_message'])
    #             })
    #         result.append(result_dict)
    #     return result


