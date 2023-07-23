from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shipping_payment_token_ids = fields.One2many(
        string="Payment Tokens",
        comodel_name='payment.token',
        inverse_name='shipping_id')
    property_card_fee = fields.Float(
        string='Credit Card Fee Percentage', company_dependent=True,
        )

    def create_new_token(self):
        return self.sudo().env.ref('authorize_extension.action_generate_payment_token_wizard').read()[0]

    def get_authorize_token(self):
        self.ensure_one()
        return self.sudo().payment_token_ids.filtered(lambda rec: rec.acquirer_id.provider == 'authorize')[:1]

    @api.onchange('street', 'street2', 'city', 'state_id', 'zip', 'zip_id', 'country_id')
    def onchange_address(self):
        if self._origin.id:
            token_domain = ['|', ('address_id', '=', self._origin.id), ('partner_id', '=', self._origin.id)]
            token_count = self.env['payment.token'].search_count(token_domain)
            if token_count:
                token_ids = self.env['payment.token'].search(token_domain)
                msg = f'Address is used in Payment Tokens:\n %s ' % ', '.join(token_ids.mapped('name'))
                return {
                    'warning': {'title': 'Warning!', 'message': msg}}

    def write(self, vals):
        token_domain = ['|', ('address_id', 'in', self._origin.ids), ('partner_id', 'in', self._origin.ids)]
        address_fields = ['street', 'street2', 'city', 'state_id', 'zip', 'zip_id', 'country_id']
        res = super(ResPartner, self).write(vals)
        if self._origin.ids:
            if res and any(key in address_fields for key in vals) and self.env['payment.token'].search_count(token_domain):
                self.message_post(body="Address modified")
                if self.parent_id:
                    self.parent_id.message_post(body="[%s]\'s address modified" % self.display_name)
        return res


ResPartner()
