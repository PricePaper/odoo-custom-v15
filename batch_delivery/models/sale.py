# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    have_price_lock = fields.Boolean(compute='_compute_price_lock')
    delivery_date = fields.Date(string="Delivery Date")
    batch_warning = fields.Text(string='Shipment Progress wrarning Message', copy=False)

    @api.depends('order_line.price_lock')
    def _compute_price_lock(self):
        for rec in self:
            rec.have_price_lock = any(rec.order_line.mapped('price_lock'))

    def action_cancel(self):
        self.ensure_one()
        if not self._context.get('from_cancel_wizard'):
            if self.invoice_ids and self.invoice_ids.filtered(lambda r: r.state == 'posted'):
                raise ValidationError('Cannot perform this action, invoice not in draft state')
            if self.picking_ids and self.picking_ids.filtered(lambda r: r.state in ('in_transit', 'done')):
                if not self.env.user.has_group('account.group_account_manager') and not self.env.user.has_group('sales_team.group_sale_manager'):
                    raise ValidationError('You don\'t have permissions to cancel a SO with DO in transit.\nContact your system administrator')
            return {
                'name': 'Cancel Sales Order',
                'view_mode': 'form',
                'res_model': 'sale.order.cancel',
                'view_id': self.env.ref('sale.sale_order_cancel_view_form').id,
                'type': 'ir.actions.act_window',
                'context': {'default_order_id': self.id},
                'target': 'new'
            }

        return super(SaleOrder, self).action_cancel()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    info = fields.Char(compute='_get_price_lock_info_JSON')

    @api.depends('product_id')
    def _get_price_lock_info_JSON(self):
        for line in self:
            line.info = json.dumps(False)
            if line.product_id and line.price_from and line.price_from.price_lock:
                # price_from = self.price_from.mapped('price_lock')[0]
                info = {
                    'title': 'Price locked until %s' % line.price_from.lock_expiry_date.strftime('%m/%d/%Y'),
                    'record': line.price_from.id
                }
                line.info = json.dumps(info)

    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom', 'move_ids.quantity_done')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            if line.order_id.storage_contract:
                qty = 0.0
                print(line.sudo().purchase_line_ids)
                for po_line in line.sudo().purchase_line_ids:
                    print(po_line, po_line.state, sum(po_line.move_ids.filtered(lambda s: s.state != 'cancel').mapped('quantity_done')))
                    if po_line.state in ('purchase', 'done', 'received'):
                        qty += sum(po_line.move_ids.filtered(lambda s: s.state != 'cancel').mapped('quantity_done'))
                line.qty_delivered = qty

            elif line.qty_delivered_method == 'stock_move':
                qty = 0.0
                outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
                for move in outgoing_moves:
                    if move.state == 'done':
                        qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom,
                                                                  rounding_method='HALF-UP')
                    elif move.picking_id.state == 'in_transit':
                        qty_done = sum(move.move_orig_ids.filtered(lambda rec: rec.state == 'done').mapped('product_uom_qty'))
                        qty += move.product_uom._compute_quantity(qty_done, line.product_uom,
                                                                  rounding_method='HALF-UP')
                for move in incoming_moves:
                    if move.state == 'done':
                        qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom,
                                                                  rounding_method='HALF-UP')
                    elif move.picking_id.state == 'in_transit':
                        qty -= move.product_uom._compute_quantity(move.quantity_done, line.product_uom,
                                                                  rounding_method='HALF-UP')
                line.qty_delivered = qty

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Override to add a context value to identify in transit
        """
        self = self.with_context(from_sale=True)
        res =  super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
        for line  in self:
            transit_move = line.move_ids.mapped('move_orig_ids')
            transit_move.write({'transit_picking_id': transit_move.mapped('move_dest_ids').mapped('picking_id')})
        return res

    @api.onchange('product_id')
    def _onchange_product_id_set_lot_domain(self):
        available_lot_ids = []
        if self.order_id.warehouse_id and self.product_id:
            location = self.order_id.warehouse_id.lot_stock_id
            quants = self.env['stock.quant'].read_group([
                ('product_id', '=', self.product_id.id),
                ('location_id', 'child_of', location.id),
                ('quantity', '>', 0),
                ('lot_id', '!=', False),
            ], ['lot_id'], 'lot_id')
            available_lot_ids = [quant['lot_id'][0] for quant in quants]
        self.lot_id = False
        return {
            'domain': {'lot_id': [('id', 'in', available_lot_ids)]}
        }

    @api.onchange('lot_id', 'product_uom_qty')
    def _onchange_product_id_lot_qty_warning(self):
        if self.lot_id and self.lot_id.quant_ids:
            quants = self.lot_id.quant_ids.filtered(lambda q: q.location_id.usage in ['internal'])
            product_qty = sum(quants.mapped('quantity'))
            if product_qty < self.product_uom_qty:
                return {
                    'warning': {
                        'title': 'Warning!',
                        'message': 'Please note that there are only %s quantities of %s currently in this lot' % (product_qty, self.product_id.name)
                    }
                }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
