from odoo import models,fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shipping_payment_token_ids = fields.One2many(
        string="Payment Tokens", comodel_name='payment.token', inverse_name='shipping_id')

    def create_new_token(self):
        return self.sudo().env.ref('authorize_extension.action_generate_payment_token_wizard').read()[0]

    def get_authorize_token(self):
        self.ensure_one()
        return self.payment_token_ids.filtered(lambda rec: rec.acquirer_id.provider == 'authorize')[:1]
ResPartner()
