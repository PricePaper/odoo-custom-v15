from odoo import fields, models, api


class OrderBanner(models.Model):
    _name = 'order.banner'
    _description = 'Banner to be added in processed Sale orders'

    code = fields.Char('Order Code',copy=False)
    name = fields.Char(string='Banner Description',required=True)
