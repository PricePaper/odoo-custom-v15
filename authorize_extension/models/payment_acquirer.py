# -*- coding: utf-8 -*-

from odoo import fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    is_avs_check = fields.Boolean('Check AVS')
