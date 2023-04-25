# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    have_price_lock = fields.Boolean(compute='_compute_price_lock')
    delivery_date = fields.Date(string="Delivery Date")
    #batch_warning = fields.Text(string='Shipment Progress wrarning Message', copy=False)
    order_banner_id = fields.Many2one('order.banner',string='Shipment Progress warning Message',copy=False)
    sale_default_message = fields.Html(related="company_id.sale_default_message", readonly=True)

    def write(self, values):
        if values.get('partner_shipping_id'):
            for record in self:
                new_partner = self.env['res.partner'].browse(values.get('partner_shipping_id'))
                picking = record.mapped('picking_ids').filtered(lambda x: x.state not in ('done', 'cancel'))
                if picking:
                    picking.write({'partner_id':new_partner.id})
        res = super(SaleOrder, self).write(values)
        return res

    @api.onchange('partner_shipping_id')
    def _onchange_partner_shipping_id(self):
        return {}


    def _get_action_view_picking(self, pickings):
        """
        view for sales man
        """
        action = super(SaleOrder, self)._get_action_view_picking(pickings)
        if self.env.user.user_has_groups('sales_team.group_sale_salesman') and (not self.env.user.user_has_groups('stock.group_stock_user') or not self.env.user.user_has_groups('account.group_account_invoice')):
            form_view = [(self.env.ref('batch_delivery.view_picking_form_inherited_pricepaper').id, 'form')]
            tree_view = [(self.env.ref('stock.vpicktree').id, 'tree')]
            if len(pickings) > 1:
                action['views'] = tree_view + form_view
            elif pickings:
                action['views'] = form_view
            if action.get('context'):
                action['context']['edit'] = False
            else:
                action['context'] = {'create': False, 'edit': False}
        return action

    @api.depends('order_line.price_lock')
    def _compute_price_lock(self):
        for rec in self:
            rec.have_price_lock = any(rec.order_line.mapped('price_lock'))

    def action_cancel(self):
        self.ensure_one()
        if not self._context.get('from_cancel_wizard'):
            if self.invoice_ids and self.invoice_ids.filtered(lambda r: r.state == 'posted'):
                raise ValidationError('Cannot perform this action, invoice not in draft state')
            if self.picking_ids and self.picking_ids.filtered(lambda r: r.state in ('in_transit', 'done', 'transit_confirmed')):
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

    @api.ondelete(at_uninstall=False)
    def _unlink_except_confirmed(self):
        pass

    def remove_move_lines(self):
        move = self.mapped('move_ids').filtered(lambda r: r.state != 'cancel')
        transit_move = self.mapped('move_ids').mapped('move_orig_ids').filtered(lambda r: r.state != 'cancel')
        if transit_move and transit_move.picking_id.state in ['in_transit''done']:
            raise UserError(
                _('You can not remove an order line once stock move is done'))

        elif any(transit_moves.state in ('cancel', 'waiting', 'done') for transit_moves in transit_move):
            raise UserError(_('You can only delete draft moves.'))

        elif any(moves.state in ('cancel', 'waiting', 'done') for moves in move):
            raise UserError(_('You can only delete draft moves.'))
        else:
            cancel_moves  = transit_move+move
            cancel_moves.sudo()._action_cancel()
            cancel_moves.sudo().unlink()

    def unlink(self):
       for record in self:
           if not record.is_delivery and record.order_id.state!='draft':
                record.remove_move_lines()
       return super(SaleOrderLine, self).unlink()

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
                for po_line in line.sudo().purchase_line_ids:
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
                    elif move.picking_id.state in ('in_transit', 'transit_confirmed'):
                        # qty_done = sum(move.move_orig_ids.filtered(lambda rec: rec.state == 'done').mapped('product_uom_qty'))
                        qty += move.product_uom._compute_quantity(move.quantity_done, line.product_uom, rounding_method='HALF-UP')
                for move in incoming_moves:
                    if move.state == 'done':
                        qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom,
                                                                  rounding_method='HALF-UP')
                    elif move.picking_id.state in ('in_transit', 'transit_confirmed'):
                        qty -= move.product_uom._compute_quantity(move.quantity_done, line.product_uom, rounding_method='HALF-UP')
                line.qty_delivered = qty

    def update_move_quantity(self, previous_product_uom_qty):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                continue
            product_qty = line.product_uom_qty - qty
            outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
            for move in outgoing_moves.filtered(lambda rec: rec.state not in ('cancel', 'done')):
                need_to_process = True
                if any(move.mapped('move_orig_ids').sudo().mapped('created_purchase_line_id').mapped('order_id').filtered(lambda rec: rec.state  != 'draft')):
                    continue
                for transit_move in move.mapped('move_orig_ids').filtered(lambda rec: rec.state not in ('cancel', 'done')):
                    transit_move._do_unreserve()
                    transit_move.write({'product_uom_qty': transit_move.product_uom_qty + product_qty})
                    transit_move._action_assign()
                    if transit_move.created_purchase_line_id and transit_move.created_purchase_line_id.order_id.state == 'draft':
                        transit_move.created_purchase_line_id.sudo().write({'product_qty': transit_move.product_uom_qty})
                    need_to_process = False
                    break
                if not (need_to_process and move.mapped('move_orig_ids')):
                    move.write({'product_uom_qty': move.product_uom_qty + product_qty})


    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Override to add a context value to identify in transit
        """
        self.update_move_quantity(previous_product_uom_qty)
        self = self.with_context(from_sale=True)
        res =  super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
        for line in self:
            transit_move = line.move_ids.mapped('move_orig_ids').filtered(lambda rec: not rec.transit_picking_id)
            picking_id = transit_move.mapped('move_dest_ids').mapped('picking_id').filtered(lambda rec: rec.state not in ('cancel', 'done', 'in_transit', 'transit_confirmed'))
            if len(picking_id) > 1:
                picking_id = picking_id[0]
            transit_move.write({'transit_picking_id': picking_id.id})
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

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        move_id = self.move_ids.filtered(lambda rec: rec.quantity_done == self.qty_to_invoice and rec.picking_id.is_return is False and rec.state != 'cancel')
        if len(move_id) > 1:
            move_id = move_id[0]
        res.update({'stock_move_id': move_id.id})
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

    def _update_price_post(self, values):
        orders = self.mapped('order_id')
        for order in orders:
            order_lines = self.filtered(lambda x: x.order_id == order)
            msg = "<b>" + _("Price unit has been updated.") + "</b><ul>"
            for line in order_lines:
                msg += "<li> %s: <br/>" % line.product_id.display_name
                msg += _(
                    "Unit Price: %(old_qty)s -> %(new_qty)s",
                    old_qty=line.price_unit,
                    new_qty=values["price_unit"]
                ) + "<br/>"
            msg += "</ul>"
            order.message_post(body=msg)

    def _update_tax_valuess(self, values):
        orders = self.mapped('order_id')
        for order in orders:
            order_lines = self.filtered(lambda x: x.order_id == order)
            msg = "<b>" + _("Tax has been updated for.") + "</b><ul>"
            for line in order_lines:
                msg += "<li> %s: <br/>" % line.product_id.display_name
            msg += "</ul>"
            order.message_post(body=msg)

    def _update_product_post(self, old_product):

        msg = "<b>" + _("Product has been changed.") + "</b><ul>"
        msg += "<li> %s: <br/>" % self.product_id.display_name
        msg += _(
            "Product: %(old)s -> %(new)s",
            old=old_product.display_name,
            new=self.product_id.display_name
        ) + "<br/>"
        msg += "</ul>"
        self.order_id.message_post(body=msg)

    def write(self, values):
        if 'product_id' in values:
            old_product = self.product_id
        else:
            if 'product_uom_qty' in values:
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                self.filtered(
                    lambda r: r.state != 'sale' and float_compare(r.product_uom_qty, values['product_uom_qty'],
                                                              precision_digits=precision) != 0)._update_line_quantity(values)
            if 'price_unit' in values:
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                if float_compare(self.price_unit, values['price_unit'], precision_digits=precision) != 0:
                    self._update_price_post(values)
        tax_id = self.tax_id.ids
        result = super(SaleOrderLine, self).write(values)
        if 'product_id' in values:
            self._update_product_post(old_product)
        if tax_id and tax_id != self.tax_id.ids:
            self._update_tax_valuess(values)
        return result
