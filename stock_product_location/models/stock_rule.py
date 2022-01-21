# -*- coding: utf-8 -*-

from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        """
        Update Source LOcation By Product/product Category Stock Location
        """
        res = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, company_id, values)
        location_src = product_id and product_id.property_stock_location and \
                       product_id.property_stock_location.id or product_id and \
                       product_id.categ_id and product_id.categ_id.property_stock_location and \
                       product_id.categ_id.property_stock_location.id or False

        if location_src:
            res.update({'location_id': location_src})
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
