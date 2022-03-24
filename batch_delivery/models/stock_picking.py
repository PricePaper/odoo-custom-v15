# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    _order = 'release_date, deliver_by'

    truck_driver_id = fields.Many2one('res.partner', string='Truck Driver', copy=False)
    route_id = fields.Many2one('truck.route', string='Truck Route', group_expand='_read_group_route_ids', copy=False)
    is_delivered = fields.Boolean(string='Delivered', copy=False)
    state = fields.Selection(selection_add=[('in_transit', 'In Transit')])
    street = fields.Char(string='Street', related='partner_id.street')
    street2 = fields.Char(string='Street2', related='partner_id.street2')
    city = fields.Char(string='City', related='partner_id.city')
    state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id')
    zip = fields.Char(string='Zip', related='partner_id.zip')
    delivery_notes = fields.Text(string='Delivery Notes', related='partner_id.delivery_notes')
    item_count = fields.Float(string="Item Count", compute='_compute_item_count')
    partner_loc_url = fields.Char(string="Partner Location", related='partner_id.location_url')
    release_date = fields.Date(related='sale_id.release_date', string="Earliest Delivery Date", store=True)
    deliver_by = fields.Date(related='sale_id.deliver_by', string="Deliver By", store=True)
    shipping_easiness = fields.Selection([('easy', 'Easy'), ('neutral', 'Neutral'), ('hard', 'Hard')], compute="_compute_shipping_easiness",
                                         string='Easiness Of Shipping')
    is_transit = fields.Boolean(string='Transit', copy=False)
    is_late_order = fields.Boolean(string='Late Order', copy=False)
    reserved_qty = fields.Float('Available Quantity', compute='_compute_available_qty')
    low_qty_alert = fields.Boolean(string="Low Qty", compute='_compute_available_qty')
    sequence = fields.Integer(string='Order', default=1)
    is_invoiced = fields.Boolean(string="Invoiced", compute='_compute_state_flags')
    invoice_ref = fields.Char(string="Invoice Reference", compute='_compute_invoice_ref')
    invoice_ids = fields.Many2many('account.move', compute='_compute_invoice_ids',store=True)
    is_return = fields.Boolean(compute='_compute_state_flags')
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", tracking=True)
    batch_id = fields.Many2one(
        'stock.picking.batch', string='Batch Picking', check_company=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Batch associated to this picking', copy=False, tracking=True)
    is_internal_transfer = fields.Boolean(string='Internal transfer')
    transit_date = fields.Date()
    transit_move_lines = fields.One2many('stock.move', 'transit_picking_id', string="Stock Moves", copy=False)



    @api.depends('state')
    def _compute_show_validate(self):
        for picking in self:
            if not (picking.immediate_transfer) and picking.state == 'draft':
                picking.show_validate = False
            elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned', 'in_transit'):
                picking.show_validate = False
            else:
                picking.show_validate = True

    @api.depends('move_lines.sale_line_id.order_id.release_date')
    def _compute_scheduled_date(self):
        for picking in self:
            release_date = []
            if picking.move_lines.mapped('sale_line_id').mapped('order_id'):
                release_date = picking.move_lines.mapped('sale_line_id').mapped('order_id').mapped('release_date')
            if picking.move_type == 'direct':
                if self.rma_id:
                    self.scheduled_date = fields.Datetime.now()
                elif release_date and any(release_date):
                    picking.scheduled_date = datetime.combine(min(release_date), datetime.min.time())
                elif picking.move_lines.mapped('date'):
                    picking.scheduled_date = min(picking.move_lines.mapped('date'))
                else:
                    picking.scheduled_date = fields.Datetime.now()
            else:

                if self.rma_id:
                    self.scheduled_date = fields.Datetime.now()
                elif release_date and any(release_date):
                    picking.scheduled_date = datetime.combine(min(release_date), datetime.min.time())
                elif picking.move_lines.mapped('forecast_expected_date'):
                    picking.scheduled_date = min(picking.move_lines.mapped('forecast_expected_date'))
                else:
                    picking.scheduled_date = fields.Datetime.now()

    @api.depends('sale_id.invoice_status', 'invoice_ids', 'invoice_ids.state')
    def _compute_state_flags(self):
        for pick in self:
            if pick.transit_move_lines:
                pick.is_return = False
            elif pick.move_lines.mapped('move_orig_ids').ids:
                pick.is_return = True
                pick.is_invoiced = True
            else:
                pick.is_return = False
            if pick.sale_id.invoice_status in ['invoiced', 'no']:
                pick.is_invoiced = True
            else:
                pick.is_invoiced = False

    @api.depends('sale_id.invoice_ids', 'move_lines')
    def _compute_invoice_ids(self):
        for rec in self:
            rec.invoice_ids = rec.sale_id.invoice_ids.filtered(lambda r: rec in r.picking_ids)



    def _compute_invoice_ref(self):
        for rec in self:
            rec.invoice_ref = False
            if rec.invoice_ids:
                rec.invoice_ref = rec.invoice_ids[-1].name

    @api.depends('move_lines.reserved_availability')
    def _compute_available_qty(self):
        for pick in self:
            moves = pick.mapped('move_lines').filtered(lambda move: move.state != 'cancel')
            pick.reserved_qty = sum(moves.mapped('forecast_availability'))
            pick.low_qty_alert = pick.item_count != pick.reserved_qty and pick.state != 'done'

    @api.depends('partner_id.change_delivery_days', 'partner_id.zip_shipping_easiness')
    def _compute_shipping_easiness(self):
        for picking in self:
            if picking.partner_id:
                if picking.partner_id.change_delivery_days:
                    picking.shipping_easiness = picking.partner_id.shipping_easiness
                else:
                    picking.shipping_easiness = picking.partner_id.zip_shipping_easiness
            else:
                picking.shipping_easiness = False

    def _compute_item_count(self):
        for picking in self:
            count = 0
            for line in picking.move_lines:
                count += line.product_uom_qty
            picking.item_count = count

    @api.depends('move_type', 'is_delivered', 'move_lines.picking_id', 'is_transit', 'immediate_transfer', 'move_lines.state', )
    def _compute_state(self):
        """
            override state compute method for adding transit in selection
        """
        not_in_transit = self.env['stock.picking']
        for picking in self:
            if picking.is_transit and not all(move.state in ['cancel', 'done'] for move in picking.move_lines):
                picking.state = 'in_transit'
            else:
                not_in_transit |= picking
        return super(StockPicking, not_in_transit)._compute_state()

    @api.model
    def create(self, vals):
        if vals.get('is_internal_transfer'):
            if vals.get('location_dest_id'):
                vals['location_dest_id'] = False
        return super().create(vals)

    # def action_transit_validate(self):
    #     self.
    def _action_generate_backorder_wizard(self, show_transfers=False):
        """
          Delivery order don't need to create an active back order. Always cancel back order
          new view added for this
        """
        view = self.env.ref('batch_delivery.view_cancel_back_order_form')

        code = self.mapped('picking_type_code')
        if isinstance(code, list) and len(code) > 0:
            code = code[0]
        if code != 'incoming':
            res = super()._action_generate_backorder_wizard(show_transfers)
            res.update({
                'views': [(view.id, 'form')],
                'view_id': view.id,
            })
            return res
        return super()._action_generate_backorder_wizard(show_transfers)

    def validate_multiple_delivery(self):
        for rec in self:
            if rec.state != 'in_transit' and not rec.purchase_id:
                raise UserError("Some of the selected Delivery order is not in transit state")
            rec.button_validate()
        return {'type': 'ir.actions.act_window_close'}
        #return self

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
            if not product.property_stock_location:
                continue
            self.env['stock.move'].create({'product_id': product.id,
                                           'picking_id': self.id,
                                           'name': product.name,
                                           'location_id': self.location_id.id,
                                           'product_uom': product.uom_id.id,
                                           'location_dest_id': product.property_stock_location.id,
                                           'product_uom_qty': qty
                                           })

    def action_assign_transit(self):
        if not self.transit_move_lines:
            raise UserError("Nothing to check the availability for.")
        return self.transit_move_lines._action_assign()

    def action_make_transit(self):
        for picking in self:
            if picking.state not in ['in_transit', 'done']:
                if not any(picking.transit_move_lines.mapped('quantity_done')):
                    raise UserError("You cannot transit if no quantities are  done.\nTo force the transit, switch in edit mode and encode the done quantities.")
                picking.transit_move_lines.filtered(lambda rec: rec.quantity_done > 0).with_context(is_transit=True)._action_done(cancel_backorder=True)
                # picking.transit_move_lines.filtered(lambda rec: rec.quantity_done == 0)._action_cancel()
                for move in picking.transit_move_lines.filtered(lambda rec: rec.state =='done'):
                    move.move_dest_ids.write({'quantity_done': move.product_uom_qty})
                picking.write({
                    'is_transit': True,
                    'transit_date': fields.Date.context_today(picking)
                })
                if picking.batch_id:
                    picking.sale_id.write({'delivery_date': picking.batch_id.date})
        return True

    @api.model
    def default_get(self, default_fields):
        result = super(StockPicking, self).default_get(default_fields)
        if self._context.get('from_internal_transfer_action'):
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal'), ('name', '=', 'Internal Transfers')], limit=1)
            if picking_type:
                result['picking_type_id'] = picking_type.id
        return result

    # def action_validate(self):
    #     self.ensure_one()
    #     pass

    def action_validate_internal(self):
        self.ensure_one()
        return self.button_validate()

    @api.model
    def _read_group_route_ids(self, routes, domain, order):
        """
              This method used to show the routes in assign route kanban.

              :param routes: default param
              :param domain: default param
              :param order: default param
              :returns: active truck routes record set
              :raises UserError: raises an exception if search/ read is allowed
          """
        return self.env['truck.route'].search([('set_active', '=', True)])

    def create_invoice(self):
        for picking in self:
            if not any([line.quantity_done for line in picking.move_lines]):
                raise UserError(_('Please enter done quantities in %s before proceed..' % picking.name))
            if picking.sale_id.invoice_status in ['no', 'invoiced']:
                continue
            if picking.sale_id.invoice_status == 'to invoice':
                # picking.sale_id.adjust_delivery_line()
                picking.sale_id._create_invoices(final=True)
                picking.is_invoiced = True
            if picking.batch_id:
                invoice = picking.sale_id.invoice_ids.filtered(lambda rec: picking in rec.picking_ids)
                invoice.write({'invoice_date': picking.batch_id.date})
            for inv in picking.sale_id.invoice_ids.filtered(lambda rec: rec.state == 'draft'):
                # if not inv.journal_id.sequence_id:
                #     raise UserError(_('Please define sequence on the journal related to this invoice.'))
                picking.invoice_ref = inv.name

    def write(self, vals):
        # res = super(StockPicking, self).write(vals)
        for picking in self:
            if 'route_id' in vals.keys() and picking.batch_id and picking.batch_id.state in ('done', 'no_payment', 'paid'):
                raise UserError("Batch is already in done state. You can not remove the picking")
            route_id = vals.get('route_id', False)
            if route_id:
                batch = self.env['stock.picking.batch'].search([('state', '=', 'in_progress'), ('route_id', '=', route_id)], limit=1)
                if batch:
                    picking.action_make_transit()
                elif not batch:
                    batch = self.env['stock.picking.batch'].search([('state', 'in', ('draft', 'in_truck')), ('route_id', '=', route_id)], limit=1)
                if batch:
                    picking.sale_id.write({'delivery_date': batch.date})
                    if batch.state in ('in_truck', 'in_progress'):
                        picking.mapped('sale_id').write({'batch_warning': 'This order has already been processed for shipment', 'state': 'done'})
                    if picking.is_invoiced:
                        invoice = picking.sale_id.invoice_ids.filtered(lambda rec: picking in rec.picking_ids)
                        invoice.write({'invoice_date': batch.date})

                if not batch:
                    batch = self.env['stock.picking.batch'].create({'route_id': route_id})
                picking.batch_id = batch

                vals['is_late_order'] = batch.state == 'in_progress'
            if 'route_id' in vals.keys() and not (
                    vals.get('route_id', False)) and picking.batch_id and picking.batch_id.state == 'draft':
                vals.update({'batch_id': False})
            if 'route_id' in vals.keys() and not vals.get('route_id', False):
                vals.update({'batch_id': False, 'is_late_order': False, 'is_transit': False})
                picking.mapped('sale_id').write({'batch_warning': '', 'state': 'sale'})
        return super().write(vals)

    def _action_done(self):
        res = super()._action_done()
        for pick in self:
            pick.is_transit = False
        for line in self.move_line_ids.filtered(lambda r: r.state == 'done'):
            line.product_onhand_qty = line.product_id.qty_available + line.product_id.transit_qty
        return res

    def check_return_reason(self):
        move_lines = self.move_lines.filtered(lambda m: m.quantity_done < m.product_uom_qty and not m.reason_id)
        if move_lines:
            default_reason = self.env.ref('batch_delivery.default_stock_picking_return_reason', raise_if_not_found=False)
            if default_reason:
                move_lines.write({'reason_id': default_reason.id})
            else:
                products = move_lines.mapped('product_id')
                if products:
                    msg = '⚠ 𝐘𝐨𝐮 𝐧𝐞𝐞𝐝 𝐭𝐨 𝐞𝐧𝐭𝐞𝐫 𝐭𝐡𝐞 𝐬𝐭𝐨𝐜𝐤 𝐫𝐞𝐭𝐮𝐫𝐧 𝐫𝐞𝐚𝐬𝐨𝐧 𝐟𝐨𝐫 𝐏𝐫𝐨𝐝𝐮𝐜𝐭 \n'
                    for i, product in enumerate(products, 1):
                        msg += '\t\t%d. %s\n' % (i, product.display_name)
                    raise UserError(msg)

    def action_validate(self):
        self.ensure_one()
        if self.picking_type_id.code == 'outgoing' and not self.purchase_id:
            self.check_return_reason()
        return self.button_validate()

    def action_cancel(self):
        for rec in self:
            if self.mapped('invoice_ids').filtered(lambda r: rec in r.picking_ids and r.state == 'posted'):
                raise UserError("Cannot perform this action, invoice not in draft state")
            if not self._context.get('back_order_cancel', False):
                self.mapped('invoice_ids').filtered(lambda r: rec in r.picking_ids).sudo().button_cancel()
            else:
                self.mapped('invoice_ids').remove_zero_qty_line()
            if rec.transit_move_lines:
                rec.transit_move_lines._action_cancel()
        res = super(StockPicking, self).action_cancel()
        self.write({'batch_id': False, 'is_late_order': False})
        return res

    def action_print_invoice(self):
        invoices = self.mapped('invoice_ids').filtered(lambda r: r.state != 'cancel')
        if not invoices:
            raise UserError('Nothing to print.')

        if self.batch_id and self.batch_id.truck_driver_id and not self.batch_id.truck_driver_id.firstname:
            raise UserError('Missing firstname from driver: %s' % self.batch_id.truck_driver_id.name)

        return self.env.ref('batch_delivery.ppt_account_selected_invoices_report').report_action(docids=invoices.ids, config=False)

    def action_print_pick_ticket(self):
        return self.env.ref('batch_delivery.batch_picking_active_report').report_action(self)

    def action_print_product_label(self):
        return self.env.ref('batch_delivery.product_label_report').report_action(self)

    def action_remove(self):
        return self.write({'batch_id': False, 'route_id': False, 'is_late_order': False, 'is_transit': False})

    def do_print_picking(self):
        self.write({'printed': True})
        return self.env.ref('batch_delivery.batch_picking_active_report').report_action(self)

    def receive_product_in_lines(self):

        for line in self.transit_move_lines:
            if not line.quantity_done and line.state != 'cancel':
                if self.picking_type_code == 'incoming':
                    line.quantity_done = line.product_uom_qty
                elif self.picking_type_code == 'outgoing':
                    line.quantity_done = line.reserved_availability
        if self.picking_type_code == 'incoming':
            for line in self.move_lines:
                if not line.quantity_done and line.state != 'cancel':
                    if self.picking_type_code == 'incoming':
                        line.quantity_done = line.product_uom_qty


    @api.model
    def reset_picking_with_route(self):
        picking = self.env['stock.picking'].search(
            [('state', 'in', ['confirmed', 'assigned', 'in_transit','waiting']), ('batch_id', '!=', False),
             ('batch_id.state', '=', 'draft')])
        picking.mapped('route_id').write({'set_active': False})
        # removed newly created batch with empty pciking lines.
        picking.mapped('batch_id').unlink()
        for rec in picking:
            rec.write({'batch_id':False,'route_id':False})
        return True


    def make_picking_done(self):
        for picking in self:
            self.env['stock.backorder.confirmation'].with_context(button_validate_picking_ids=picking.id).create({
                'pick_ids': [(4, p.id) for p in picking],
                'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': True, 'picking_id': p.id}) for p in picking]
            }).process_cancel_backorder()

    def button_validate(self):
        """
        if there are movelines with reserved quantities
        and not validated, automatically validate them.
        """
        self.ensure_one()

        if self.picking_type_id.code == 'outgoing':
            for line in self.move_line_ids:
                if line.lot_id and line.pref_lot_id and line.lot_id != line.pref_lot_id:
                    raise UserError(
                        "This Delivery for product %s is supposed to use products from the lot %s please clear the Preferred Lot field to override" % (
                            line.product_id.name, line.pref_lot_id.name))
            # todo not need this methods now.
            # no_quantities_done_lines = self.move_line_ids.filtered(lambda l: l.qty_done == 0.0 and not l.is_transit)
            # for line in no_quantities_done_lines:
            #     if line.move_id and line.move_id.product_uom_qty == line.move_id.reserved_availability:
            #         line.qty_done = line.product_uom_qty

        return super(StockPicking, self).button_validate()

    # @api.model
    # def reset_picking_with_route(self):
    #     picking = self.env['stock.picking'].search(
    #         [('state', 'in', ['confirmed', 'waiting', 'assigned', 'in_transit']), ('batch_id', '!=', False), ('batch_id.state', '=', 'draft')])
    #     picking.mapped('route_id').write({'set_active': False})
    #     # removed newly created batch with empty pciking lines.
    #     picking.mapped('batch_id').sudo().unlink()
    #     return picking.write({'route_id': False})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
