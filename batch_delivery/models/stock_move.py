# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    picking_status = fields.Char(string='Picking Status', compute='_compute_picking_state')
    delivery_notes = fields.Text(string='Delivery Notes', related='partner_id.delivery_notes')
    delivery_move_id = fields.Many2one('stock.move', string='Delivery for Move')
    delivery_picking_id = fields.Many2one('stock.picking', string='Delivery for Picking', readonly=True,
                                          related='delivery_move_id.picking_id')
    is_transit = fields.Boolean(string='Transit')
    qty_update = fields.Float(String="Reset Logic",
                              help="* Use \'Negative\' value if you want to Decrease the Reserved Qty.\n"
                                   "* Use \'Positive\' value if you want to Increase the Reserved Qty.")
    qty_available = fields.Float(String="Available Quantity", compute='_compute_qty_available')
    partner_id = fields.Many2one('res.partner', compute='_compute_partner_id', string="Partner", readonly=True)

    @api.depends('sale_line_id.order_id.partner_shipping_id')
    def _compute_partner_id(self):
        for move in self:
            move.partner_id = move.sale_line_id.order_id.partner_shipping_id

    @api.depends('location_id', 'qty_update')
    def _compute_qty_available(self):
        for move in self:
            move.qty_available = move.product_id.with_context(location=move.location_id.id).qty_available

    @api.multi
    def _compute_picking_state(self):
        for move in self:
            move.picking_status = move.picking_id and move.picking_id.state or ''

    @api.multi
    def action_reset(self):
        """
        Reset the reserved quantity with reset logic values.
        Negative value for decrease,
        Positive value for increase.
        """
        quant = self.env['stock.quant']
        for move in self:
            available_qty = quant._get_available_quantity(product_id=move.product_id, location_id=move.location_id)

            if available_qty <= 0 and move.qty_update > 0:
                raise UserError(_(
                    'It is not possible to reserve more products of %s than you have in stock.') % move.product_id.display_name)
            elif move.reserved_availability <= 0 and move.qty_update < 0:
                raise UserError(_(
                    'It is not possible to unreserve more products of %s than you have in stock.') % move.product_id.display_name)
            elif move.qty_available < move.qty_update:
                raise UserError(_('Choose a value less than available quantity.'))
            elif move.qty_update < 0 and move.reserved_availability < abs(move.qty_update):
                raise UserError(_('Not enough reserved quantity..!'))
            else:
                query = dict(
                    need=move.qty_update,  # reset logic (-ve or +ve) as per reset logic
                    available_quantity=available_qty,  # available product quantity from current location
                    location_id=move.location_id,  # location used in stock move
                    strict=False  # enable uom based quantity conversion
                )
                move._update_reserved_quantity(**query)
                move.quantity_done = move.reserved_availability
                if not move.reserved_availability:
                    move.state = 'confirmed'
                elif move.reserved_availability < move.product_uom_qty:
                    move.state = 'partially_available'
                else:
                    move.state = 'assigned'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """updates the move line values
           with preferred lot id
        """
        res = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if self.sale_line_id and self.sale_line_id.lot_id:
            res.update({'pref_lot_id': self.sale_line_id.lot_id.id})
        return res

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None,
                                  owner_id=None, strict=True):
        """if a lot is preffered then use that lot for reserving the stock move
           also check the quantities currently available for that lot in doing so.
        """
        if self.sale_line_id and self.sale_line_id.lot_id:
            avail_qty = self.sale_line_id.lot_id.product_qty
            if avail_qty > self.sale_line_id.product_uom_qty:
                lot_id = self.sale_line_id.lot_id
        res = super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id, lot_id=lot_id,
                                                               package_id=package_id, owner_id=owner_id, strict=strict)
        return res


StockMove()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
