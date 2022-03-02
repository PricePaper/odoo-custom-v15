# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_transit_location = fields.Boolean(string='Transit Location')

    @api.model
    def create_missing_in_transit_rules(self):
        """
        method to create/ update transit rules
        """
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        transit_location = self.env.ref('batch_delivery.stock_location_in_transit')
        if transit_location.location_id != warehouse.view_location_id:
            transit_location.write({'location_id': warehouse.view_location_id.id})
        category_all = self.env.ref('product.product_category_all')
        if warehouse.delivery_route_id not in category_all.route_ids:
            category_all.write({'route_ids': [(4, warehouse.delivery_route_id.id)]})
        if self.env['stock.rule'].search_count([('location_id', '=', transit_location.id)]) > 0:
            return True
        update_id = warehouse.delivery_route_id.rule_ids.id
        mto_route = self.env.ref('stock.route_warehouse0_mto')
        customer_location = self.env.ref('stock.stock_location_customers')
        mto_rule = mto_route.rule_ids.filtered(lambda rec: rec.location_id == customer_location)

        warehouse.delivery_route_id.write({
            'rule_ids':[
                (0, 0, {
                    "name": "WH: Stock → Transit",
                    'active': True,
                    'procure_method': 'make_to_stock',
                    'action': 'pull',
                    'auto': 'manual',
                    'location_id': transit_location.id,
                    'location_src_id': warehouse.lot_stock_id.id,
                    'picking_type_id': warehouse.out_type_id.id,
                    'sequence': 18

                }),
                (1, update_id, {
                    "name": "WH: Transit → Customer",
                    'location_src_id': transit_location.id,
                    'procure_method': 'make_to_order',
                    'sequence': 10,
                })
            ]
        })
        mto_route.write({
            'rule_ids': [
                (0, 0, {
                    "name": "WH: Stock → Transit (MTO)",
                    'active': True,
                    'procure_method': 'make_to_order',
                    'action': 'pull',
                    'auto': 'manual',
                    'location_id': transit_location.id,
                    'location_src_id': warehouse.lot_stock_id.id,
                    'picking_type_id': warehouse.out_type_id.id,
                    'sequence': 10

                }),
                (1, mto_rule.id,  {
                    "name": "WH: Transit → Customers (MTO)",
                    "location_src_id": transit_location.id,
                })
            ]
        })
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
