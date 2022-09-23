# -*- coding: utf-8 -*-

from odoo import fields, models


class PaymentToken(models.Model):
    _name = 'payment.token'
    _inherit = ['payment.token', 'mail.thread']

    authorize_profile = fields.Char(
        string="Authorize.Net Profile ID",
        help="The unique reference for the partner/token combination in the Authorize.net backend.",
        tracking=True)
    acquirer_ref = fields.Char(
        string="Acquirer Reference", help="The acquirer reference of the token of the transaction",
        required=True, tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    shipping_id = fields.Many2one('res.partner', "Delivery address")
    address_id = fields.Many2one('res.partner', "Billing address")


PaymentToken()
