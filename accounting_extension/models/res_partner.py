from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    payment_token_ids = fields.One2many('payment.token', 'partner_id', string='Payment Token')
    property_payment_method_id = fields.Many2one(
        comodel_name='account.payment.method',
        string='Payment Method',
        company_dependent=True,
        domain="[('payment_type', 'in', ('outbound', 'inbound'))]",
    )
