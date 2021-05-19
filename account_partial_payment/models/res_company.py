# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    cash_discount_id = fields.Many2one('account.account', string='Cash Discount Account',
                                       domain=[('deprecated', '=', False)],
                                       help="This account will be used to post the cash discount")
    vendor_discount_id = fields.Many2one('account.account', string='Vendor Discount Account',
                                         domain=[('deprecated', '=', False)],
                                         help="This account will be used to post the vendor discount")


ResCompany()
