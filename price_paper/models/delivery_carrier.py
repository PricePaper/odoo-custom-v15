# -*- coding: utf-8 -*-

from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    average_company_cost = fields.Float(string='Average Company Cost',
                                        help='The Average amount that costs for the company to make this delivery.',
                                        default=80.00)


DeliveryCarrier()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
