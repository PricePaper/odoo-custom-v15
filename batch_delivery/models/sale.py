# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    have_price_lock = fields.Boolean(compute='_compute_price_lock')
    delivery_date = fields.Date(string="Delivery Date")
    cancel_reason = fields.Text(string='Cancel Reason')
    batch_warning = fields.Text(string='Shipment Progress wrarning Message', copy=False)

    @api.depends('order_line.price_lock')
    def _compute_price_lock(self):
        for rec in self:
            rec.have_price_lock = any(rec.order_line.mapped('price_lock'))

    def action_cancel(self):
        for order in self:
            if not self._context.get('from_cancel_wizard'):
                if order.invoice_ids and order.invoice_ids.filtered(lambda r: r.state == 'posted'):
                    raise ValidationError(_('Cannot perform this action, invoice not in draft state'))
                if order.picking_ids and order.picking_ids.filtered(lambda r: r.state in ('in_transit', 'done')):
                    if not self.env.user.has_group('account.group_account_manager') and not self.env.user.has_group(
                            'sales_team.group_sale_manager'):
                        raise ValidationError(
                            _('You don\'t have permissions to cancel a SO with DO in transit. \n\
                            Only Sales Manager and Accounting adviser have the permission.'))
                view_id = self.env.ref('batch_delivery.view_so_cancel_reason_wiz').id
                return {
                    'name': _('Sale Order Cancel Reason'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'so.cancel.reason',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'target': 'new'
                }

        return super(SaleOrder, self).action_cancel()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    info = fields.Char(compute='_get_price_lock_info_JSON')
    pre_delivered_qty = fields.Float(default=0.00, copy=False)

    @api.depends('product_id')
    def _get_price_lock_info_JSON(self):
        for line in self:
            line.info = json.dumps(False)
            if line.product_id and line.price_from and line.price_from.price_lock:
                # price_from = self.price_from.mapped('price_lock')[0]
                # print(self.price_from.mapped('price_lock'),self.price_from)
                info = {
                    'title': 'Price locked until %s' % line.price_from.price_lock.lock_expiry_date.strftime('%m/%d/%Y'),
                    'record': line.price_from.id}
                line.info = json.dumps(info)

    # todo by default system handles theis things
    # def write(self, vals):
    #     for line in self:
    #         if 'product_uom_qty' in vals:
    #             precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #             lines = self.filtered(
    #                 lambda r: r.state == 'sale' and not r.is_expense and float_compare(r.product_uom_qty,
    #                                                                                    vals['product_uom_qty'],
    #                                                                                    precision_digits=precision) == 1)
    #             for order_line in lines:
    #                 moves = order_line.move_ids.filtered(lambda r: r.state not in ('cancel', 'done'))
    #                 if moves and len(moves) == 1:
    #                     moves._do_unreserve()
    #                     moves.product_uom_qty = vals['product_uom_qty']
    #     res = super(SaleOrderLine, self).write(vals)
    #     return res
# todo lot is not used right now
# @api.onchange('product_id')
# def _onchange_product_id_set_lot_domain(self):
#     available_lot_ids = []
#     if self.order_id.warehouse_id and self.product_id:
#         location = self.order_id.warehouse_id.lot_stock_id
#         quants = self.env['stock.quant'].read_group([
#             ('product_id', '=', self.product_id.id),
#             ('location_id', 'child_of', location.id),
#             ('quantity', '>', 0),
#             ('lot_id', '!=', False),
#         ], ['lot_id'], 'lot_id')
#         available_lot_ids = [quant['lot_id'][0] for quant in quants]
#     self.lot_id = False
#     return {
#         'domain': {'lot_id': [('id', 'in', available_lot_ids)]}
#     }
#
# @api.onchange('lot_id')
# def _onchange_product_id_lot_qty_warning(self):
#     if self.lot_id and self.lot_id.quant_ids:
#         quants = self.lot_id.quant_ids.filtered(lambda q: q.location_id.usage in ['internal'])
#         product_qty = sum(quants.mapped('quantity'))
#
#         warning_mess = {
#             'title': _('Warning!'),
#             'message': _('Please note that there are only %s quantities of %s currently in this lot' % (
#                 product_qty, self.product_id.name))
#         }
#         res = {'warning': warning_mess}
#         return res
# todo stock move ids is a compute one now
# @api.multi
# def _prepare_invoice_line(self, qty):
#     self.ensure_one()
#     result = super(SaleOrderLine, self)._prepare_invoice_line(qty)
#     moves = self.mapped('move_ids').filtered(lambda rec: rec.state not in ['cancel'])
#     if moves:
#         result.update({'stock_move_ids': [(6, 0, moves.ids)]})
#     return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
