# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    default_code = fields.Char(string='Internal Reference', related='product_id.default_code')


SupplierInfo()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
