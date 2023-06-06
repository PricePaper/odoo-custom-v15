# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleReport(models.Model):
    _inherit = 'sale.report'

    def _from_sale(self, from_clause=''):
        from_ = super(SaleReport, self)._from_sale()
        from_ = from_.replace("uom_id", 'ppt_uom_id')
        return from_

