# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleReport(models.Model):
    _inherit = 'sale.report'

    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        select_ = super(SaleReport, self)._select_sale(fields)
        select_ = select_.replace('t.uom_id', 't.ppt_uom_id')
        return select_

    def _from_sale(self, from_clause=''):
        from_ = super(SaleReport, self)._from_sale()
        from_ = from_.replace("uom_id", 'ppt_uom_id')
        return from_

    def _group_by_sale(self, groupby=''):
        groupby_ = super()._group_by_sale(groupby)
        groupby_ = groupby_.replace('t.uom_id', 't.ppt_uom_id')
        return groupby_

