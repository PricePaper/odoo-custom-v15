# -*- coding: utf-8 -*-

from odoo import models, fields, _


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    average_company_cost = fields.Float(string='Average Company Cost',
                                        help='The Average amount that costs for the company to make this delivery.',
                                        default=80.00)
    min_profit = fields.Float('Minimum Profit')

    def rate_shipment(self, order):
        """
        Override original method to add some extra fields in return dict
         cost: actual price
         carrier_price: price with margin
        """
        self.ensure_one()
        if hasattr(self, '%s_rate_shipment' % self.delivery_type):
            res = getattr(self, '%s_rate_shipment' % self.delivery_type)(order)
            # return actual price for profit calculation
            if self.delivery_type not in ['fixed', 'based_on_rule']:
                res['cost'] = res['price']
            # apply margin on computed price
            res['price'] = float(res['price']) * (1.0 + (self.margin / 100.0))
            # save the real price in case a free_over rule override it to 0
            res['carrier_price'] = res['price']
            # free when order is large enough
            if res['success'] and self.free_over and order._compute_amount_total_without_delivery() >= self.amount:
                res['warning_message'] = _('The shipping is free since the order amount exceeds %.2f.') % (self.amount)
                res['price'] = 0.0
            return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
