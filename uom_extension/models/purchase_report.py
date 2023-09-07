# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    def _select(self):
        select_str = super(PurchaseReport, self)._select()
        select_str = select_str.replace('t.uom_id', 't.ppt_uom_id')
        return select_str

    def _from(self):
        from_str = super(PurchaseReport, self)._from()
        from_str = from_str.replace('uom_id', 'ppt_uom_id')
        return from_str

    def _group_by(self):
        group_by_str = super(PurchaseReport, self)._group_by()
        group_by_str = group_by_str.replace('t.uom_id', 't.ppt_uom_id')
        return group_by_str