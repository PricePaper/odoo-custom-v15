# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_select_supplier(self, values, suppliers):
        """Overridden to select Primary vendor from suppliers.
        """
        supplier = suppliers.filtered('is_primary_vendor')[0]
        if not supplier:
            supplier = suppliers[0]
        return supplier

StockRule()
