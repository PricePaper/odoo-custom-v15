# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_compare


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_select_supplier(self, values, suppliers):
        """Overridden to select Primary vendor from suppliers.
        """
        if values.get('orderpoint_id', False):
            res = self.env['product.supplierinfo']
            order_point = values.get('orderpoint_id')
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            for seller in suppliers.filtered(lambda seller: seller.is_available):
                quantity_uom_seller = abs(
                    order_point.product_id.qty_available - (order_point.product_max_qty or order_point.product_min_qty))
                if quantity_uom_seller and order_point.product_uom and order_point.product_uom != seller.product_uom:
                    quantity_uom_seller = order_point.product_uom._compute_quantity(quantity_uom_seller,
                                                                                    seller.product_uom)
                if float_compare(quantity_uom_seller, seller.min_qty, precision_digits=precision) == -1:
                    continue
                res |= seller
                break
            if not res:
                return super(StockRule, self)._make_po_select_supplier(values, suppliers)
            return res
        return super(StockRule, self)._make_po_select_supplier(values, suppliers)


StockRule()


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    is_available = fields.Boolean(string='Is Available', compute='_compute_supplierinfo_avl', store=True)

    @api.depends('date_start', 'date_end')
    def _compute_supplierinfo_avl(self):
        date = fields.Date.context_today(self)
        for seller in self:
            if seller.date_start and seller.date_start > date:
                seller.is_available = False
            elif seller.date_end and seller.date_end < date:
                seller.is_available = False
            else:
                seller.is_available = True


SupplierInfo()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
