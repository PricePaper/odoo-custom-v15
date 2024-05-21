# -*- coding: utf-8 -*-

from odoo import fields, models, api


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
    is_default = fields.Boolean('Default Token')
    card_type = fields.Char(string="Card Type", required=True)

    @api.model
    def create(self, vals):
        """
        if token is created as default uncheck all the
        previous default token for that partner (if exists)
        """


        result = super(PaymentToken, self).create(vals)
        if result.is_default:
            if result.shipping_id:
                existing_defaults = self.search(
                    [('shipping_id', '=', result.shipping_id.id), ('id', '!=', result.id), ('is_default', '=', True)])
            else:
                existing_defaults = self.search([('partner_id', '=', result.partner_id.id),
                    ('shipping_id', '=', False), ('id', '!=', result.id), ('is_default', '=', True)])
            if existing_defaults:
                existing_defaults.write({'is_default': False})
        return result

    def write(self, vals):

        res = super(PaymentToken, self).write(vals)
        if vals.get('is_default'):
            for record in self:
                if record.is_default:
                    if record.shipping_id:
                        existing_defaults = self.search([('shipping_id', '=', record.shipping_id.id),
                                    ('id', '!=', record.id), ('is_default', '=', True)])
                    else:
                        existing_defaults = self.search([('partner_id', '=', record.partner_id.id),
                                ('shipping_id', '=', False),
                                ('id', '!=', record.id), ('is_default', '=', True)])
                    if existing_defaults:
                        existing_defaults.write({'is_default': False})
        return res


PaymentToken()
