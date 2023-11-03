# -*- coding: utf-8 -*-

from odoo import models, fields, api
from collections import defaultdict

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_lines.reserved_availability')
    def _compute_available_qty(self):
        for pick in self:
            moves = pick.mapped('transit_move_lines').filtered(lambda move: move.state != 'cancel')
            if pick.state in ('in_transit', 'transit_confirmed'):
                moves = pick.mapped('move_lines').filtered(lambda move: move.state != 'cancel')
            res_qty = 0
            for move in moves:
                if move.forecast_availability:
                    res_qty += move.product_id.uom_id._compute_quantity(move.forecast_availability, move.product_uom)
            pick.reserved_qty = res_qty
            pick.low_qty_alert = pick.item_count != pick.reserved_qty and pick.state != 'done'

    @api.depends('move_line_ids', 'move_line_ids.result_package_id', 'move_line_ids.product_uom_id',
                 'move_line_ids.qty_done')
    def _compute_bulk_weight(self):
        """
        overridden to fix shipping_weight in picking, use ppt_uom_id if available else uom_id
        @return:
        """
        picking_weights = defaultdict(float)
        # Ordering by qty_done prevents the default ordering by groupby fields that can inject multiple Left Joins in the resulting query.
        res_groups = self.env['stock.move.line'].read_group(
            [('picking_id', 'in', self.ids), ('product_id', '!=', False), ('result_package_id', '=', False)],
            ['id:count'],
            ['picking_id', 'product_id', 'product_uom_id', 'qty_done'],
            lazy=False, orderby='qty_done asc'
        )
        products_by_id = {
            product_res['id']: (product_res['ppt_uom_id'][0], product_res['uom_id'][0], product_res['weight'])
            for product_res in
            self.env['product.product'].with_context(active_test=False).search_read(
                [('id', 'in', list(set(grp["product_id"][0] for grp in res_groups)))], ['ppt_uom_id', 'uom_id', 'weight'])
        }
        for res_group in res_groups:
            ppt_uom_id, uom_id, weight = products_by_id[res_group['product_id'][0]]

            uom = self.env['uom.uom'].browse(ppt_uom_id or uom_id)
            product_uom_id = self.env['uom.uom'].browse(res_group['product_uom_id'][0])
            picking_weights[res_group['picking_id'][0]] += (
                    res_group['__count']
                    * product_uom_id._compute_quantity(res_group['qty_done'], uom)
                    * weight
            )
        for picking in self:
            picking.weight_bulk = picking_weights[picking.id]
