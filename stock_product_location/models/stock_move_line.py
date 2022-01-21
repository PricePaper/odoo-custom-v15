# -*- coding: utf-8 -*-

from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.onchange('product_id', 'product_uom_id')
    def _onchange_product_id(self):
        """
        Update Source/Destination Location by Product/Catgory Stock Location
        """
        res = super(StockMoveLine, self)._onchange_product_id()
        if self.product_id:
            product_loc_id = self.product_id.property_stock_location.id or self.product_id.categ_id.property_stock_location.id or ''
            if self.location_id.usage == 'supplier':
                self.location_dest_id = product_loc_id
            else:
                self.location_id = product_loc_id
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
