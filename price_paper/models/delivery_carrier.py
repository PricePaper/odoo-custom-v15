# -*- coding: utf-8 -*-

from odoo import models, fields, _


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    average_company_cost = fields.Float(string='Average Company Cost', default=80.00,
                                        help='The Average amount that costs for the company to make this delivery.')
    min_profit = fields.Float('Minimum Profit')

    def rate_shipment(self, order):
        """
        Override original method to add some extra fields in return dict
         cost: actual price
         carrier_price: price with margin
        """
        res = super().rate_shipment(order)
        if self.delivery_type not in ['fixed', 'based_on_rule']:

            res['cost'] = res['price'] * (100/(100 + self.margin))
        # # apply margin on computed price
        # if res['price']:
        #     res['price'] = float(res['price']) * (1.0 + (self.margin / 100.0))
        #     # save the real price in case a free_over rule override it to 0
        #     res['carrier_price'] = res['price']
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
