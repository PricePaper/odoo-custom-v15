# -*- coding: utf-8 -*-

from odoo import models, api


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        """
        Update Source Location By Product/product Category Stock Location
        """
        res = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, company_id, values)
        if self.picking_type_id.code == 'outgoing' and not self.location_src_id.is_transit_location and self._context.get('from_sale'):
            location_src = product_id and product_id.property_stock_location and \
                           product_id.property_stock_location.id or product_id and \
                           product_id.categ_id and product_id.categ_id.property_stock_location and \
                           product_id.categ_id.property_stock_location.id or False

            if location_src:
                res.update({'location_id': location_src})
        return res


StockRule()


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def _get_rule_domain(self, location, values):
        """
        remove bin location and add parent to avoid confusion in selecting rule
        """
        res = super()._get_rule_domain(location, values)
        if values.get('warehouse_id') and location in values.get(
                'warehouse_id').lot_stock_id.child_internal_location_ids:
            for domain in res:
                if domain[0] == 'location_id':
                    res.insert(res.index(domain),
                               ('location_id', domain[1], values.get('warehouse_id').lot_stock_id.id))
                    res.remove(domain)
        return res


ProcurementGroup()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
