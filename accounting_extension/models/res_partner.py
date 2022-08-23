from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    payment_token_ids = fields.One2many('payment.token', 'partner_id', string='Payment Token')



