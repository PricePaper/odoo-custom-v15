from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def create_new_token(self):
        return self.env.ref('authorize_extension.action_generate_payment_token_wizard').read()[0]

    def get_authorize_token(self):
        self.ensure_one()
        return self.payment_token_ids.filtered(lambda rec: rec.acquirer_id.provider == 'authorize')[:1]
ResPartner()
