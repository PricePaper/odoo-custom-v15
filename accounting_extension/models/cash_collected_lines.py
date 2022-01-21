from odoo import fields, models, api, _
from odoo.exceptions import UserError

from odoo.addons import decimal_precision as dp


class CashCollectedLines(models.Model):
    _inherit = 'cash.collected.lines'

    discount = fields.Float(string='Discount(%)')
    discount_amount = fields.Float(string='Discount', digits='Product Price')




class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_discount_limit = fields.Float(
        string='Customer Discount Limit',
        config_parameter='accounting_extension.customer_discount_limit',
        default=5.0
    )
