# -*- coding: utf-8 -*-

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.onchange('product_id')
    def product_id_change(self):
        """
        Update Source/Destination Location by Product/Catgory Stock Location
        """
        if self.product_id:
            product_loc_id = self.product_id.property_stock_location.id or self.product_id.categ_id.property_stock_location.id or ''
            if self.location_id:
                if self.location_id.usage == 'supplier':
                    self.location_dest_id = product_loc_id
            else:
                self.location_id = product_loc_id


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
