# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    default_code = fields.Char(string='Internal Reference', related='product_id.default_code')



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    supplier_month_increment = fields.Integer(string='Number Of Months', config_parameter='purchase_extension.supplier_month_increment')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
