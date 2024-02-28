# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from collections import defaultdict

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _purchase_order_picking_confirm_message_content(self, picking, purchase_dict):
        if not purchase_dict:
            purchase_dict = {}
        title = _("Receipt confirmation %s") % (picking.name)
        message = "<h3>%s</h3>" % title
        message += _(
            "The following items have now been received in Incoming Shipment %s:"
        ) % (picking.name)
        message += "<ul>"
        for purchase_line_id in purchase_dict.values():
            display_name = purchase_line_id["purchase_line"].product_id.display_name
            product_qty = purchase_line_id["stock_move"].product_uom_qty
            uom = purchase_line_id["stock_move"].product_uom.name
            message += _(
                "<li><b>%(display_name)s</b>: Received quantity %(product_qty)s %(uom)s</li>",
                display_name=display_name,
                product_qty=product_qty,
                uom=uom,
            )
        message += "</ul>"
        return message

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


    def load_products(self):
        self.ensure_one()
        self.move_lines.unlink()
        if not self.location_id:
            raise UserError("Source location should be selected")
        quants = self.env['stock.quant'].search([('location_id', '=', self.location_id.id)])
        quants = quants.filtered(lambda r: r.quantity - r.reserved_quantity > 0)
        for quant in quants:
            product = quant.mapped('product_id')
            qty = quant.quantity - quant.reserved_quantity
            qty = product.uom_id._compute_quantity(qty, product.ppt_uom_id)
            if not product.property_stock_location:
                continue
            self.env['stock.move'].create({'product_id': product.id,
                                           'picking_id': self.id,
                                           'name': product.name,
                                           'location_id': self.location_id.id,
                                           'product_uom': product.ppt_uom_id.id,
                                           'location_dest_id': product.property_stock_location.id,
                                           'product_uom_qty': qty
                                           })
    def _action_done(self):
        res = super()._action_done()
        for line in self.move_line_ids.filtered(lambda r: r.state == 'done'):
            line.product_onhand_qty = line.product_id.quantity_available + line.product_id.transit_qty
        return res
