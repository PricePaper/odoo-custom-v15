# -*- coding: utf-8 -*-

from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    show_in_route = fields.Boolean(string='Show in assign route', default=False)
    late_order_product = fields.Many2one('product.product', string='Late order product')


DeliveryCarrier()
