# -*- coding: utf-8 -*-
import math
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from operator import itemgetter
from itertools import groupby
from odoo.tools.misc import clean_context, OrderedSet
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "mail.thread", "mail.activity.mixin"]

    delivery_notes = fields.Text(string='Delivery Notes', related='partner_id.delivery_notes')
    # is_transit = fields.Boolean(string='Transit')
    qty_update = fields.Float(string="Reset Logic")
    reason_id = fields.Many2one('stock.picking.return.reason', string='Reason  For Return (Stock)')
    qty_to_transfer = fields.Float(string="Qty in Location", compute='_compute_qty_to_transfer', store=False)
    unit_price = fields.Float(string="Unit Price", copy=False, compute='_compute_total_price')
    total = fields.Float(string="Subtotal", copy=False, compute='_compute_total_price', store=False)
    transit_picking_id = fields.Many2one('stock.picking', 'Transit Picking', copy=False)
    product_uom_qty = fields.Float(tracking=True)
    quantity_done = fields.Float(tracking=True)
    invoice_line_ids = fields.Many2many(comodel_name='account.move.line', compute="_get_aml_ids", string="Invoice Lines")
    is_reason_added = fields.Boolean("Is Reason added?", compute="_compute_reason_needed")

    @api.depends('quantity_done', 'product_uom_qty', 'reason_id')
    def _compute_reason_needed(self):
        for move in self:
            move.is_reason_added = False
            if move.transit_picking_id.picking_type_code == 'outgoing':
                if not move.reason_id and move.quantity_done < move.product_uom_qty:
                    move.is_reason_added = True
                else:
                    move.is_reason_added = False

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'picking_id': self.picking_id.id,
            'company_id': self.company_id.id,
        }
        if quantity:
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom, rounding_method='HALF-UP')
            uom_quantity = float_round(uom_quantity, precision_digits=rounding)
            uom_quantity_back_to_product_uom = self.product_uom._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
            vals = dict(vals, product_uom_qty=uom_quantity)
        #     if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
        #         vals = dict(vals, product_uom_qty=uom_quantity)
        #     else:
        #         vals = dict(vals, product_uom_qty=quantity, product_uom_id=self.product_id.uom_id.id)
        package = None
        if reserved_quant:
            package = reserved_quant.package_id
            vals = dict(
                vals,
                location_id=reserved_quant.location_id.id,
                lot_id=reserved_quant.lot_id.id or False,
                package_id=package.id or False,
                owner_id =reserved_quant.owner_id.id or False,
            )
        if not vals.get('product_uom_qty'):
            return vals
        if vals['product_uom_qty'] > self.product_uom_qty:
            vals['product_uom_qty'] = self.product_uom_qty
        elif vals['product_uom_qty'] < self.product_uom_qty:
            difference = self.product_uom_qty - vals['product_uom_qty']
            if difference < 0.008:
                vals['product_uom_qty'] = self.product_uom_qty
        return vals

    def get_quantity(self, field='quantity_done', alternative_feild='quantity_done'):
        qty = 0
        for move in self:
            if getattr(move, field):
                qty += getattr(move, field)
            elif getattr(move, alternative_feild):
                qty += getattr(move, alternative_feild)
        return qty

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        #todo remove after go live (odo can't proces the current move and old move
        res = super()._prepare_merge_moves_distinct_fields()
        for field in ['description_picking', 'date_deadline']:
            if field in res:
                res.remove(field)
        return res

    def _get_aml_ids(self):
        for line in self:
            line.invoice_line_ids = []
            aml_ids = self.env['account.move.line'].search([('stock_move_id', '=', line.id)]).ids
            if not aml_ids and line.sale_line_id and not line.rma_id and not (line.picking_id.backorder_id or line.transit_picking_id.backorder_id):
                aml_ids = line.sale_line_id.mapped('invoice_lines').ids
            if aml_ids:
                line.invoice_line_ids = [[6, 0, aml_ids]]
        return {}

    def _account_entry_move(self, qty, description, svl_id, cost):
        self.ensure_one()
        if self.picking_id.transit_date:
            return super(StockMove, self.with_context(force_period_date=self.picking_id.transit_date))._account_entry_move(qty, description, svl_id,
                                                                                                                           cost)
        return super()._account_entry_move(qty, description, svl_id, cost)

    @api.onchange('product_id')
    def onchange_product_id_internal_transfer(self):
        if self.picking_id and self.picking_id.is_internal_transfer:
            if self.product_id:
                self.location_dest_id = self.product_id.property_stock_location.id or self.product_id.categ_id.property_stock_location.id or ''
                self.location_id = self.picking_id.location_id and self.picking_id.location_id or False
            else:
                self.location_dest_id = False

    @api.depends('quantity_done')
    def _compute_total_price(self):
        for move in self:
            move.total = 0
            move.unit_price = 0
            if move.picking_id.picking_type_id.code == 'outgoing':
                move.unit_price = -move.price_unit
            elif move.picking_id.picking_type_id.code == 'incoming':
                move.unit_price = move.price_unit
            if move.picking_id.is_customer_return:
                move.unit_price = move.product_id.standard_price
            if move.state != 'cancel':
                move.total = move.unit_price * move.quantity_done

    @api.depends('product_id', 'picking_id.location_id')
    def _compute_qty_to_transfer(self):
        quant = self.env['stock.quant']
        for move in self:
            move.qty_to_transfer = 0
            if move.product_id and move.picking_id and move.picking_id.location_id:
                quant = quant.search([('product_id', '=', move.product_id.id), ('location_id', '=', move.picking_id.location_id.id)], limit=1)
                if quant:
                    qty = quant.quantity - quant.reserved_quantity
                    move.qty_to_transfer = move.product_id.uom_id._compute_quantity(qty, move.product_uom, rounding_method='HALF-UP')

    def action_cancel_move(self):
        """
        wrapper class for _action_cancel private method
        """
        self._action_cancel()
        return True

    def _should_be_assigned(self):
        res = super()._should_be_assigned()
        if res and self.location_dest_id.is_transit_location and self.picking_type_id.code == 'outgoing' and self._context.get('from_sale'):
            return False
        if self._context.get('is_transit'):
            return False
        return res

    def action_reset(self, qty=0):
        """
        Reset the reserved quantity with reset logic values.
        Negative value for decrease,
        Positive value for increase.
        """

        for move in self:
            # qty_available always shows the quanity in requested (UOM).
            to_qty = qty
            # if self.product_uom != self.product_id.uom_id:
            #     qty = self.product_uom._compute_quantity(qty, self.product_id.uom_id)
            reserved_qty = move.reserved_availability
            try:
                for ml in move.filtered(lambda rec: rec.procure_method == 'make_to_order').move_line_ids:
                    if ml.qty_done:
                        ml.qty_done = 0
                move._do_unreserve()
            except UserError as e:
                for ml in move.move_line_ids:
                    quants = self.env['stock.quant']._gather(ml.product_id, ml.location_id, lot_id=ml.lot_id, package_id=ml.package_id,
                                                             owner_id=ml.owner_id, strict=True)
                    available_quantity = sum(quants.mapped('reserved_quantity'))
                    rounding_digit = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                    available_quantity = float_round(available_quantity, precision_digits=rounding_digit)
                    if ml.product_uom_qty > available_quantity:
                        ml.with_context({'bypass_reservation_update': True}).write({'product_uom_qty': available_quantity})
                move._do_unreserve()
            available_qty = move.availability
            if available_qty < qty:
                raise UserError('It is not possible to reserve more products of %s than you have in stock.' % move.product_id.display_name)
            elif move.reserved_availability <= 0 and qty < 0:
                raise UserError('It is not possible to unreserve more products of %s than you have in stock.' % move.product_id.display_name)
            elif move.availability < qty:
                raise UserError('Choose a value less than available quantity.')
            elif qty < 0 and move.reserved_availability < abs(qty):
                raise UserError('Not enough reserved quantity..!')
            elif move.product_uom_qty < qty:
                raise UserError("Can't reserve more product than requested..!")
            else:
                if qty != 0:
                    move._action_assign_reset_qty(to_qty)
                msg = """<ul><li>
                    %s Quantity Reserved: %s <span aria-label='Changed' class='fa fa-long-arrow-right' role='img' title='Changed'/> %s
                    </li></ul>""" % (move.product_id.display_name, reserved_qty, to_qty,)
                move.message_post(
                    body=msg,
                    subtype_id=self.env.ref('mail.mt_note').id)
                move.transit_picking_id.message_post(
                    body=msg,
                    subtype_id=self.env.ref('mail.mt_note').id)
        return self

    def _action_assign_reset_qty(self, qty=0):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `product_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """

        def _get_available_move_lines(move):
            move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
            keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

            def _keys_in_sorted(ml):
                return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

            grouped_move_lines_in = {}
            for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted), key=itemgetter(*keys_in_groupby)):
                qty_done = 0
                for ml in g:
                    qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                grouped_move_lines_in[k] = qty_done
            move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move) \
                .filtered(lambda m: m.state in ['done']) \
                .mapped('move_line_ids')
            # As we defer the write on the stock.move's state at the end of the loop, there
            # could be moves to consider in what our siblings already took.
            moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
            moves_out_siblings_to_consider = moves_out_siblings & (
                    StockMove.browse(assigned_moves_ids) + StockMove.browse(partially_available_moves_ids))
            reserved_moves_out_siblings = moves_out_siblings.filtered(
                lambda m: m.state in ['partially_available', 'assigned'])
            move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped(
                'move_line_ids')
            keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

            def _keys_out_sorted(ml):
                return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

            grouped_move_lines_out = {}
            for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                qty_done = 0
                for ml in g:
                    qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                grouped_move_lines_out[k] = qty_done
            for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted),
                                key=itemgetter(*keys_out_groupby)):
                grouped_move_lines_out[k] = sum(self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
            available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for key in
                                    grouped_move_lines_in}
            # pop key if the quantity available amount to 0
            return dict((k, v) for k, v in available_move_lines.items() if v)

        StockMove = self.env['stock.move']
        assigned_moves_ids = OrderedSet()
        partially_available_moves_ids = OrderedSet()
        # Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        reserved_availability = {move: move.reserved_availability for move in self}
        roundings = {move: move.product_id.uom_id.rounding for move in self}
        move_line_vals_list = []
        for move in self.filtered(lambda m: m.state not in ['done', 'cancel']):
            rounding = roundings[move]
            missing_reserved_uom_quantity = qty - reserved_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity,
                                                                           move.product_id.uom_id,
                                                                           rounding_method='HALF-UP')
            if move._should_bypass_reservation():
                # create the move line(s) but do not impact quants
                if move.move_orig_ids:
                    available_move_lines = _get_available_move_lines(move)
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        qty_added = min(missing_reserved_quantity, quantity)
                        move_line_vals = move._prepare_move_line_vals(qty_added)
                        move_line_vals.update({
                            'location_id': location_id.id,
                            'lot_id': lot_id.id,
                            'lot_name': lot_id.name,
                            'owner_id': owner_id.id,
                        })
                        move_line_vals_list.append(move_line_vals)
                        missing_reserved_quantity -= qty_added
                        if float_is_zero(missing_reserved_quantity, precision_rounding=move.product_id.uom_id.rounding):
                            break

                if missing_reserved_quantity and move.product_id.tracking == 'serial' and (
                        move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=1))
                elif missing_reserved_quantity:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                                       ml.location_id == move.location_id and
                                                                       ml.location_dest_id == move.location_dest_id and
                                                                       ml.picking_id == move.picking_id and
                                                                       not ml.lot_id and
                                                                       not ml.package_id and
                                                                       not ml.owner_id)
                    if to_update:
                        to_update[0].product_uom_qty += move.product_id.uom_id._compute_quantity(
                            missing_reserved_quantity, move.product_uom, rounding_method='HALF-UP')
                    else:
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                assigned_moves_ids.add(move.id)
            else:
                if float_is_zero(qty, precision_rounding=move.product_uom.rounding):
                    assigned_moves_ids.add(move.id)
                elif not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity, consider the move assigned.
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves_ids.add(move.id)
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = move.package_level_id.package_id or None
                    available_quantity = move._get_available_quantity(move.location_id, package_id=forced_package_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id,
                                                                    package_id=forced_package_id, strict=False)
                    if float_is_zero(taken_quantity, precision_rounding=rounding):
                        continue
                    if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                        assigned_moves_ids.add(move.id)
                    else:
                        partially_available_moves_ids.add(move.id)
                else:
                    # Check what our parents brought and what our siblings took in order to
                    # determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                    available_move_lines = _get_available_move_lines(move)
                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
                        if available_move_lines.get((move_line.location_id, move_line.lot_id,
                                                     move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id,
                                                  move_line.owner_id)] -= move_line.product_qty
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        # need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                        need = move.product_uom._compute_quantity(qty, move.product_id.uom_id, rounding_method='HALF-UP')
                        # `quantity` is what is brought by chained done move lines. We double check
                        # here this quantity is available on the quants themselves. If not, this
                        # could be the result of an inventory adjustment that removed totally of
                        # partially `quantity`. When this happens, we chose to reserve the maximum
                        # still available. This situation could not happen on MTS move, because in
                        # this case `quantity` is directly the quantity on the quants themselves.
                        available_quantity = move._get_available_quantity(location_id, lot_id=lot_id,
                                                                          package_id=package_id, owner_id=owner_id,
                                                                          strict=True)
                        if float_is_zero(available_quantity, precision_rounding=rounding):
                            continue
                        taken_quantity = move._update_reserved_quantity(need, min(need, available_quantity),
                                                                        location_id, lot_id, package_id, owner_id)
                        if float_is_zero(taken_quantity, precision_rounding=rounding):
                            continue
                        if float_is_zero(need - taken_quantity, precision_rounding=rounding):
                            assigned_moves_ids.add(move.id)
                            break
                        partially_available_moves_ids.add(move.id)

        self.env['stock.move.line'].create(move_line_vals_list)
        StockMove.browse(partially_available_moves_ids).write({'state': 'partially_available'})
        StockMove.browse(assigned_moves_ids).write({'state': 'assigned'})
        if self.env.context.get('bypass_entire_pack'):
            return
        self.mapped('picking_id')._check_entire_pack()

    def action_show_reset_window(self):
        self.ensure_one()
        # self.qty_update = 0
        return {
            'name': 'Reset Logic',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.reset.quantity',
            'view_id': self.env.ref('batch_delivery.view_stock_move_rest_window').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_cancel_popup(self):
        return {
            'name': 'Cancel Move',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'res_id': self.id,
            'view_id': self.env.ref('batch_delivery.view_stock_move_cancel_window').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def update_invoice_line(self):
        self.ensure_one()
        if self.picking_id.backorder_id or self.transit_picking_id.backorder_id or self.picking_id.backorder_ids or self.transit_picking_id.backorder_ids:
            return False
        invoice_lines = self.invoice_line_ids.filtered(lambda rec: rec.move_id.state == 'draft' and rec.product_id == self.product_id)
        invoice = invoice_lines.mapped('move_id') or self.sale_line_id.order_id.invoice_ids.filtered(lambda rec: rec.state == 'draft')
        if len(invoice_lines) > 1:
            invoice_lines = invoice_lines[0]
        if invoice_lines:
            quantity = self.quantity_done
            if self._context.get('is_transit') and self.state == 'done':
                quantity = sum(self.sale_line_id.move_ids.filtered(lambda rec: rec.state == 'done').mapped('product_uom_qty'))
            invoice_lines.move_id.sudo().with_context(default_move_type='out_invoice').write(
                {'invoice_line_ids': [[1, invoice_lines.id, {'quantity': quantity}]]})

        elif invoice:
            if self.quantity_done != 0:
                vals = self.sale_line_id._prepare_invoice_line()
                invoice_lines = invoice.sudo().with_context(default_move_type='out_invoice').write({'invoice_line_ids': [[0, 0, vals]]})
        return invoice_lines

    def _action_done(self, cancel_backorder=False):
        if 'outgoing' in self.mapped('picking_type_id.code') and any(self.mapped('picking_id')) and not self._context.get('transit_qty_update'):
            for move in self:
                if move.picking_id and move.move_orig_ids and move.location_id.is_transit_location:
                    incoming_qty = sum(move.move_orig_ids.filtered(lambda rec: rec.state == 'done' and
                        not rec.location_id.is_transit_location).mapped('quantity_done'))
                    outgoing_qty = sum(move.move_orig_ids.filtered(lambda rec: rec.state == 'done' and
                        rec.location_id.is_transit_location).mapped('quantity_done'))
                    if move.quantity_done == incoming_qty - outgoing_qty:
                        continue
                    remaining_qty = move.quantity_done - incoming_qty + outgoing_qty
                    if not move.picking_id.is_create_back_order:
                        move.transit_confirm_adjustment(remaining_qty)
        res = super()._action_done(cancel_backorder)
        for move in self.filtered(lambda rec: rec.state == 'done'):
            move.update_invoice_line()
        return res


    def transit_confirm_adjustment(self, remaining_qty):

        location_id = self.move_orig_ids.mapped('location_id')[0]
        location_src_id = self.location_id
        if remaining_qty > 0:
            location_id, location_src_id = location_src_id, location_id
        move_vals = {
            'name': self.name,
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': abs(remaining_qty),
            'partner_id': self.partner_id.id,
            'location_id': location_src_id.id,
            'location_dest_id': location_id.id,
            'rule_id': self.rule_id.id,
            'procure_method': 'make_to_stock',
            'origin': self.origin,
            'picking_type_id': self.picking_type_id.id,
            'group_id': self.group_id.id,
            'route_ids': [(4, route.id) for route in self.route_ids],
            'warehouse_id': self.warehouse_id.id,
            'date': fields.Datetime.now().date(),
            'date_deadline': False,
            'propagate_cancel': self.propagate_cancel,
            'description_picking': self.description_picking,
            'priority': self.priority,
            'transit_picking_id': self.picking_id.id,
            'move_dest_ids': [(4, self.id)]
        }
        new_move = self.create(move_vals)
        new_move.with_context(is_transit=True)._action_confirm()
        new_move.with_context(transit_adjustment=True).write({'quantity_done': abs(remaining_qty)})
        new_move.with_context(is_transit=True)._action_done()

    def _quantity_done_set(self):
        quantity_done = self[0].quantity_done  # any call to create will invalidate `move.quantity_done`
        for move in self:
            move_lines = move._get_move_lines()
            if not move_lines:
                if quantity_done:

                    # do not impact reservation here
                    if self._context.get('transit_adjustment') or self._context.get('move_dest_ids'):
                        move_line_vals = move._prepare_move_line_vals()
                        move_line_vals.update({'qty_done': quantity_done})
                        move_dest_ids = move.move_dest_ids
                        if not move_dest_ids:
                            move_dest_ids = self._context.get('move_dest_ids')
                        if move_dest_ids.move_line_ids.lot_id:
                            move_line_vals.update({
                                'lot_id': move_dest_ids.move_line_ids.lot_id.id,
                                'lot_name': move_dest_ids.move_line_ids.lot_id.name,
                            })
                        move_line = self.env['stock.move.line'].create(move_line_vals)
                    else:
                        move_line = self.env['stock.move.line'].create(dict(move._prepare_move_line_vals(), qty_done=quantity_done))
                    move.write({'move_line_ids': [(4, move_line.id)]})
                    move_line._apply_putaway_strategy()
            elif len(move_lines) == 1:
                move_lines[0].qty_done = quantity_done
            else:
                move._multi_line_quantity_done_set(quantity_done)


    def _transit_return(self):
        for move in self.filtered(lambda rec: rec.state == 'done'):
            if move.transit_picking_id and move.move_dest_ids:
                move_vals = {
                    'name': move.name,
                    'company_id': move.company_id.id,
                    'product_id': move.product_id.id,
                    'product_uom': move.product_uom.id,
                    'product_uom_qty': move.product_uom_qty,
                    'partner_id': move.partner_id.id,
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': move.location_id.id,
                    'rule_id': move.rule_id.id,
                    'procure_method': 'make_to_stock',
                    'origin': move.origin,
                    'picking_type_id': self.picking_type_id.id,
                    'group_id': move.group_id.id,
                    'route_ids': [(4, route.id) for route in move.route_ids],
                    'warehouse_id': move.warehouse_id.id,
                    'date': fields.Datetime.now().date(),
                    'date_deadline': False,
                    'propagate_cancel': move.propagate_cancel,
                    'description_picking': move.description_picking,
                    'priority': move.priority,
                    'transit_picking_id': move.transit_picking_id.id,
                    'picking_id': False,
                }
                new_move = self.create(move_vals)
                new_move.with_context(is_transit=True)._action_confirm()
                new_move.with_context(move_dest_ids=move.move_dest_ids).write({'quantity_done': move.product_uom_qty})
                new_move.with_context(is_transit=True)._action_done()
        return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
