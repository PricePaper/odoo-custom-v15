from odoo import fields, models, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    discount_hold = fields.Boolean(string="Discount Hold", default=False)


