# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime
from collections import defaultdict
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    _order = 'release_date, deliver_by'

    def _get_line_numbers(self):
        line_num = 1
        if self.ids:
            first_line_rec = self.browse(self.ids[0])
            for line_rec in first_line_rec.batch_id.picking_ids.sorted(key=lambda r: r.sequence):
                line_rec.line_no = line_num
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Serial Number',readonly=False, default=False)
    truck_driver_id = fields.Many2one('res.partner', string='Truck Driver', copy=False)
    route_id = fields.Many2one('truck.route', string='Truck Route', group_expand='_read_group_route_ids', copy=False)
    is_delivered = fields.Boolean(string='Delivered', copy=False)
    state = fields.Selection(selection_add=[('in_transit', 'In Transit'), ('transit_confirmed', 'Confirmed Transit')])
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
    reserved_qty = fields.Float('Available Quantity', compute='_compute_available_qty', search='_search_reserved_qty')
    low_qty_alert = fields.Boolean(string="Low Qty", compute='_compute_available_qty')
    sequence = fields.Integer(string='Order', default=1)
    is_invoiced = fields.Boolean(string="Invoiced", compute='_compute_state_flags')
    invoice_ref = fields.Char(string="Invoice Reference", compute='_compute_invoice_ref')
    invoice_ids = fields.Many2many('account.move', compute='_compute_invoice_ids')
    invoice_count = fields.Integer('Invoice count', compute='_compute_invoice_ids')
    is_return = fields.Boolean(compute='_compute_state_flags')
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", tracking=True)
    batch_id = fields.Many2one(
        'stock.picking.batch', string='Batch Picking', check_company=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Batch associated to this picking', copy=False, tracking=True)
    is_internal_transfer = fields.Boolean(string='Internal transfer')
    is_customer_return = fields.Boolean(string='Customer Return')
    transit_date = fields.Date()
    transit_move_lines = fields.One2many('stock.move', 'transit_picking_id', string="Stock Moves", copy=False)
    show_reset = fields.Boolean('Show reset button',  compute="_compute_show_reset")
    is_transit_confirmed = fields.Boolean(string='Transit Confirmed', copy=False)
    is_create_back_order = fields.Boolean(string='Create Back Order', copy=False)


    def action_transit_adjustment(self, cancel_backorder=False):

        if 'outgoing' == self.picking_type_id.code:
            for move in self.move_ids_without_package:
                move_orig_ids = move.move_orig_ids.filtered(lambda r:r.transit_picking_id == move.picking_id)
                if move_orig_ids and move.location_id.is_transit_location:
                    incoming_qty = sum(move_orig_ids.filtered(lambda rec: rec.state == 'done' and
                        not rec.location_id.is_transit_location).mapped('quantity_done'))
                    outgoing_qty = sum(move_orig_ids.filtered(lambda rec: rec.state == 'done' and
                        rec.location_id.is_transit_location).mapped('quantity_done'))
                    if move.quantity_done != incoming_qty - outgoing_qty:
                        move.transit_confirm_adjustment(move.quantity_done - incoming_qty + outgoing_qty)
        self.write({'is_transit_confirmed': True, 'is_transit': False})


    def _compute_show_reset(self):
        for picking in self:
            picking.show_reset = False
            if picking.transit_move_lines.filtered(lambda rec: rec.procure_method == 'make_to_order') and self.state not in ('done', 'cancel'):
                picking.show_reset = True

    def do_unreserve(self):
        if self.picking_type_code == 'outgoing' and not self.is_return:
            if self.transit_move_lines:
                self.transit_move_lines._do_unreserve()
                self.package_level_ids.filtered(lambda p: not p.move_ids).unlink()
        else:
            super(StockPicking, self).do_unreserve()

    def internal_move_from_customer_returned(self):
        location = self.env.user.company_id.destination_location_id
        quants = self.env['stock.quant'].search([('quantity', '>', 0.01), ('location_id', '=', location.id)])
        if quants:
            vals = {'is_locked': True,
                'picking_type_id': 5,
                'is_internal_transfer': True,
                'location_id': location.id,
                'location_dest_id': location.id,
                'move_type': 'direct',
                'company_id': 1,
                'partner_id': False,
                'origin': False,
                'owner_id': False,
                }
            internal_transfer = self.env['stock.picking'].create(vals)
            for quant in quants:
                if quant.product_id.property_stock_location:
                    self.env['stock.move'].create({'product_id': quant.product_id.id,
                                                   'picking_id': internal_transfer.id,
                                                   'name': quant.product_id.name,
                                                   'location_id': location.id,
                                                   'product_uom': quant.product_id.uom_id.id,
                                                   'location_dest_id': quant.product_id.property_stock_location.id,
                                                   })
            remove_moves = internal_transfer.move_ids_without_package.filtered(lambda m:float_round(m.qty_to_transfer, 2) <= 0)
            remove_moves.unlink()
            if not internal_transfer.move_ids_without_package:
                internal_transfer.unlink()
                return True
            for transfer_move in internal_transfer.move_ids_without_package:
                transfer_move.product_uom_qty = transfer_move.qty_to_transfer
            internal_transfer.action_confirm()
            internal_transfer.action_assign()
            for transfer_move in internal_transfer.move_ids_without_package:
                transfer_move.move_line_ids.qty_done =  transfer_move.product_uom_qty
            internal_transfer.button_validate()


        return True

    @api.depends('state')
    def _compute_show_validate(self):
        for picking in self:
            if not (picking.immediate_transfer) and picking.state == 'draft':
                picking.show_validate = False
            elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned', 'in_transit', 'transit_confirmed'):
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
        for picking in self:
            invoice_ids = picking.move_lines.mapped('invoice_line_ids').mapped('move_id')
            if not invoice_ids and not picking.rma_id:
                invoice_ids = picking.sale_id.invoice_ids
            picking.invoice_ids = invoice_ids
            picking.invoice_count = len(invoice_ids)



    def _compute_invoice_ref(self):
        for rec in self:
            rec.invoice_ref = False
            if rec.invoice_ids:
                rec.invoice_ref = rec.invoice_ids[-1].name

    def _search_reserved_qty(self, operator, value):
        domain = [('state', 'not in', ('draft', 'done', 'cancel')), ('carrier_id.show_in_route', '=', True)]
        picking_ids = []
        for picking in self.env['stock.picking'].search(domain):
            if picking.reserved_qty > 0:
                picking_ids.append(picking.id)
        return [('id', 'in', picking_ids)]

    @api.depends('move_lines.reserved_availability')
    def _compute_available_qty(self):
        for pick in self:
            moves = pick.mapped('transit_move_lines').filtered(lambda move: move.state != 'cancel')
            if pick.state in ('in_transit', 'transit_confirmed'):
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

    @api.depends('move_type', 'is_delivered', 'move_lines.picking_id', 'is_transit', 'immediate_transfer', 'move_lines.state', 'transit_move_lines.state', 'is_transit_confirmed')
    def _compute_state(self):
        """
            override state compute method for adding transit in selection
        """
        not_in_transit = self.env['stock.picking']
        for picking in self:
            if picking.is_transit and not all(move.state in ['cancel', 'done'] for move in picking.move_lines):
                picking.state = 'in_transit'
            elif picking.is_transit_confirmed and not all(move.state in ['cancel', 'done'] for move in picking.move_lines):
                picking.state = 'transit_confirmed'
            else:
                not_in_transit |= picking

        super(StockPicking, not_in_transit)._compute_state()

        for picking in not_in_transit:
            if picking.state == 'waiting':
                if picking.transit_move_lines:
                    picking_moves_state_map = defaultdict(dict)
                    picking_move_lines = defaultdict(set)
                    for move in picking.transit_move_lines:
                        picking_id = move.transit_picking_id
                        move_state = move.state
                        picking_moves_state_map[picking_id.id].update({
                            'any_draft': picking_moves_state_map[picking_id.id].get('any_draft', False) or move_state == 'draft',
                            'all_cancel': picking_moves_state_map[picking_id.id].get('all_cancel', True) and move_state == 'cancel',
                            'all_cancel_done': picking_moves_state_map[picking_id.id].get('all_cancel_done', True) and move_state in ('cancel', 'done'),
                        })
                        picking_move_lines[picking_id.id].add(move.id)
                    picking_id = (picking.ids and picking.ids[0]) or picking.id
                    relevant_move_state = self.env['stock.move'].browse(picking_move_lines[picking_id])._get_relevant_state_among_moves()
                    if picking.immediate_transfer and relevant_move_state not in ('draft', 'cancel', 'done'):
                        picking.state = 'assigned'
                    elif relevant_move_state == 'partially_available':
                        picking.state = 'assigned'
                    else:
                        picking.state = relevant_move_state


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
        if code != 'incoming' and not self.is_create_back_order:
            res = super()._action_generate_backorder_wizard(show_transfers)
            res.update({
                'views': [(view.id, 'form')],
                'view_id': view.id,
            })
            return res
        return super()._action_generate_backorder_wizard(show_transfers)

    def validate_multiple_delivery(self):
        for rec in self:
            if rec.state not in ('in_transit', 'transit_confirmed') and not rec.purchase_id:
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
            if picking.state not in ['in_transit', 'done', 'transit_confirmed']:
                if picking.id == int(self.env['ir.config_parameter'].sudo().get_param('exclude_transit_picking', 0)):
                    picking.write({
                        'is_transit': True,
                        'transit_date': fields.Date.context_today(picking)
                    })
                    if picking.batch_id:
                        picking.sale_id.write({'delivery_date': picking.batch_id.date})
                    continue
                if not any(picking.transit_move_lines.mapped('quantity_done')):
                    for line in picking.transit_move_lines.filtered(lambda r: r.state not in ('cancel', 'done')):
                        line.quantity_done = line.reserved_availability
                if not any(picking.transit_move_lines.mapped('quantity_done')):
                    raise UserError("You cannot transit if no quantities are  done.\nTo force the transit, switch in edit mode and encode the done quantities.")
                cancel_backorder = True
                if picking.is_create_back_order:
                    cancel_backorder = False
                picking.transit_move_lines.filtered(lambda rec: rec.quantity_done > 0).with_context(is_transit=True)._action_done(cancel_backorder=cancel_backorder)
                if not picking.is_create_back_order:
                    picking.transit_move_lines.filtered(lambda rec: rec.quantity_done == 0)._action_cancel()
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
        """
        set appropraite picking type from context
        """
        result = super(StockPicking, self).default_get(default_fields)
        if self._context.get('from_internal_transfer_action'):
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal'), ('name', '=', 'Internal Transfers')], limit=1)
            if picking_type:
                result['picking_type_id'] = picking_type.id
        elif self._context.get('from_is_customer_return_action'):
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
            if picking_type:
                result['picking_type_id'] = picking_type.id
        return result

    @api.onchange('picking_type_id', 'partner_id')
    def _onchange_picking_type(self):
        """
        set location_dest_id for the customer retun receipt
        """
        result = super(StockPicking, self)._onchange_picking_type()
        if self.is_customer_return and self.env.user.company_id.destination_location_id:
            self.location_dest_id = self.env.user.company_id.destination_location_id.id


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
            invoice = False
            if picking.sale_id.invoice_status == 'to invoice':
                # picking.sale_id.adjust_delivery_line()
                invoice = picking.sale_id.with_context({'picking_id': picking})._create_invoices(final=True)
                picking.is_invoiced = True
            if invoice:
                if picking.batch_id:
                    invoice.write({'invoice_date': picking.batch_id.date})
                else:
                    invoice.write({'invoice_date': fields.Date.context_today(picking)})
                picking.invoice_ref = invoice.name

    def write(self, vals):
        # res = super(StockPicking, self).write(vals)
        for picking in self:
            if 'route_id' in vals.keys() and picking.batch_id and picking.batch_id.state in ('done', 'no_payment', 'paid'):
                raise UserError("Batch is already in done state. You can not remove the picking")
            route_id = vals.get('route_id', False)
            route_exist = False
            if self.route_id:
                route_exist = True
            if route_id:
                batch = self.env['stock.picking.batch'].search([('state', '=', 'in_progress'), ('route_id', '=', route_id)], limit=1)
                if batch:
                    picking.action_make_transit()
                elif not batch:
                    batch = self.env['stock.picking.batch'].search([('state', 'in', ('draft', 'in_truck')), ('route_id', '=', route_id)], limit=1)
                if batch:
                    picking.sale_id.write({'delivery_date': batch.date})
                    if batch.state in ('in_truck', 'in_progress'):
                        warning = self.env['order.banner'].search(
                            [('code', '=', 'ORDER_PROCESSED')], limit=1)
                        picking.mapped('sale_id').write({'state': 'done','order_banner_id':warning.id if warning else False})
                    if picking.is_invoiced:
                        invoice = picking.invoice_ids.filtered(lambda rec:  rec.state not in ('posted', 'cancel'))
                        invoice.write({'invoice_date': batch.date})

                if not batch:
                    batch = self.env['stock.picking.batch'].create({'route_id': route_id})
                picking.batch_id = batch
                if not route_exist:
                    vals['is_late_order'] = batch.state in ('in_progress', 'in_truck')
            if 'route_id' in vals.keys() and not (
                    vals.get('route_id', False)) and picking.batch_id and picking.batch_id.state == 'draft':
                vals.update({'batch_id': False})
            if 'route_id' in vals.keys() and not vals.get('route_id', False):
                vals.update({'batch_id': False, 'is_late_order': False, 'is_transit': False})
                picking.mapped('sale_id').write({'state': 'sale','order_banner_id':False})

            if 'is_late_order' in vals.keys():
                sale_order = picking.sale_id
                invoice = picking.invoice_ids.filtered(lambda r: r.state != 'cancel')
                late_product = sale_order.carrier_id.late_order_product
                if late_product:
                    if vals.get('is_late_order', False):
                        if sale_order:
                            order_line = sale_order.mapped('order_line').filtered(lambda r: r.product_id and r.product_id == late_product)
                            sale_flag = False
                            if sale_order.state == 'done':
                                sale_order.write({'state': 'sale'})
                                sale_flag = True
                            if not order_line:
                                sale_vals = {'product_id': late_product.id,
                                        'product_uom_qty': 1,
                                        'price_unit': late_product.cost,
                                        'order_id':sale_order.id}
                                sale_order.with_context(from_late_order=True).write({'order_line':[(0, 0, sale_vals)]})
                            else:
                                sale_order.with_context(from_late_order=True).write({'order_line':[(1, order_line.id, {'product_uom_qty': 1})]})
                            if sale_flag:
                                sale_order.write({'state': 'done'})
                        order_line = sale_order.mapped('order_line').filtered(lambda r: r.product_id and r.product_id == late_product)
                        if invoice:
                            invoice_line = invoice.mapped('invoice_line_ids').filtered(lambda r: r.product_id and r.product_id == late_product)
                            if not invoice_line:
                                inv_vals = order_line[0]._prepare_invoice_line()
                                inv_vals['move_id'] = invoice.id
                                accounts = late_product.product_tmpl_id.get_product_accounts(fiscal_pos=sale_order.fiscal_position_id)
                                account = accounts['income']
                                inv_vals['account_id'] = account.id
                                invoice.write({'invoice_line_ids':[(0, 0, inv_vals)]})
                            else:
                                invoice.write({'invoice_line_ids':[(1, invoice_line.id, {'quantity':1})]})
                    else:
                        if sale_order:
                            order_line = sale_order.mapped('order_line').filtered(lambda r: r.product_id and r.product_id == late_product)
                            if order_line:
                                sale_flag = False
                                if sale_order.state == 'done':
                                    sale_order.write({'state': 'sale'})
                                    sale_flag = True
                                order_line.write({'product_uom_qty': 0})
                                if sale_flag:
                                    sale_order.write({'state': 'done'})
                        if invoice:
                            invoice_line = invoice.mapped('invoice_line_ids').filtered(lambda r: r.product_id and r.product_id == late_product)
                            if invoice_line:
                                if invoice.state == 'draft':
                                    invoice.write({'invoice_line_ids':[(1, invoice_line.id, {'quantity':0})]})


        return super().write(vals)

    def _action_done(self):
        res = super()._action_done()
        for pick in self:
            pick.is_transit = False
            pick.is_transit_confirmed = False
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
            self = self.with_context(skip_immediate=True)
        return self.button_validate()

    def action_cancel(self):

        for rec in self:
            if self.mapped('invoice_ids').filtered(lambda r:  r.state == 'posted'):
                raise UserError("Cannot perform this action, invoice not in draft state")
            if self._context.get('back_order_cancel', False) or self._context.get('from_reset_picking', False):
                self.mapped('invoice_ids').remove_zero_qty_line()
            else:
                self.mapped('invoice_ids').sudo().button_cancel()
            if rec.transit_move_lines:
                done_moves = rec.transit_move_lines.filtered(lambda move: move.state == 'done')
                (rec.transit_move_lines - done_moves)._action_cancel()
                done_moves._transit_return()
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
            [('state', 'in', ['confirmed', 'assigned', 'in_transit','waiting', 'transit_confirmed']), ('batch_id', '!=', False),
             ('batch_id.state', '=', 'draft')])
        picking.mapped('route_id').write({'set_active': False})
        # removed newly created batch with empty pciking lines.
        picking.mapped('batch_id').unlink()
        routes = self.env['truck.route'].search([('set_active', '=', True)])
        if routes:
            draft_batches = self.env['stock.picking.batch'].search([('route_id', 'in', routes.ids), ('state', '=', 'draft')])
            running_batches = self.env['stock.picking.batch'].search([('route_id', 'in', routes.ids), ('state', 'in', ('in_truck', 'in_progress'))])
            routes = routes - draft_batches.mapped('route_id') - running_batches.mapped('route_id')
            if draft_batches:
                draft_batches.mapped('route_id').write({'set_active': False})
                draft_batches.unlink()
            if routes:
                routes.write({'set_active': False})
        for rec in picking:
            rec.write({'batch_id':False,'route_id':False})
        return True


    def make_picking_done(self):
        for picking in self:
            backorder = self.env['stock.backorder.confirmation'].with_context(button_validate_picking_ids=picking.id).create({
                'pick_ids': [(4, p.id) for p in picking],
                'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': True, 'picking_id': p.id}) for p in picking]
            })
            if picking.is_create_back_order:
                backorder.process()
            else:
                backorder.process_cancel_backorder()

    def _get_overprocessed_stock_moves(self):
        self.ensure_one()
        return self.move_lines.filtered(
            lambda move: move.product_uom_qty != 0 and float_compare(move.quantity_done, move.product_uom_qty,
                                                                     precision_rounding=move.product_uom.rounding) == 1
        )

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
        if self.picking_type_id.code == 'incoming' and not self.is_return:
            if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
                view = self.env.ref('batch_delivery.view_overprocessed_transfer')
                wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.overprocessed.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            # todo not need this methods now.
            # no_quantities_done_lines = self.move_line_ids.filtered(lambda l: l.qty_done == 0.0 and not l.is_transit)
            # for line in no_quantities_done_lines:
            #     if line.move_id and line.move_id.product_uom_qty == line.move_id.reserved_availability:
            #         line.qty_done = line.product_uom_qty

        return super(StockPicking, self).button_validate()

    def action_create_refund(self):
        if all(len(line.invoice_line_ids.filtered(lambda rec: rec.move_id.state != 'cancel')) > 0 for line in self.move_lines):
            raise ValidationError("All lines are invoiced")
        journal = self.env['account.journal'].search([('company_id', '=', self.company_id.id), ('type', '=', 'sale')], limit=1)
        vals = {
            'ref': 'Credit Memo of: %s' % self.name,
            'date': self.scheduled_date,
            'invoice_date': self.scheduled_date,
            'journal_id': journal and journal.id,
            'invoice_user_id': self.user_id.id,
            'invoice_origin':  self.origin,
            'move_type': 'out_refund',
            'partner_id': self.partner_id.id,
            'fiscal_position_id': self.partner_id.property_account_position_id,
            'partner_shipping_id': self.partner_id.id,
            'invoice_address_id': self.partner_id.id,
            'is_customer_return':True,
        }
        line_ids = []
        sequence = 0
        for move in self.move_lines:
            accounts = move.product_id.product_tmpl_id.get_product_accounts()
            line_ids.append((0, 0, {
                'account_id': accounts['income'],
                'sequence': sequence,
                'name': move.name,
                'quantity': move.product_uom_qty,
                'price_unit':move.unit_price,
                'amount_currency': move.unit_price,
                'partner_id': self.partner_id.id,
                'product_uom_id': move.product_uom.id,
                'product_id': move.product_id.id,
                'recompute_tax_line': True,
                'stock_move_id': move.id,
                 }))
            sequence += 1
        vals.update({'invoice_line_ids': line_ids})
        refund = self.env['account.move'].create(vals)
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_refund_type")
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        action['views'] = form_view
        action['res_id'] = refund.id
        return action

    def action_view_invoice(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_refund_type")
        invoices = self.invoice_ids
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        return action

    def action_reset_picking(self):
        return {
            'name': _('Reset Picking'),
            'view_mode': 'form',
            'res_model': 'reset.picking.reason',
            'view_id': self.env.ref('batch_delivery.picking_reset_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_picking_id': self.id},
            'target': 'new'
            }


    def reset_picking(self):
        """
        Cancel this picking and create a new one
        link with sales order without cancelling the order
        link with invoice and PO if any
        """
        #todo if PO doen the orgin is not mapping in transit state.
        # raise exception if more than one picking is there bcz we cannot handle multi
        self.ensure_one()
        if self.state not in ('done', ''): #in_transit
            #copy th exisiting PO and recipt move details before cancelling
            po_id = {
                move.id: (move.move_orig_ids.mapped('created_purchase_line_id').id, move.move_orig_ids.mapped('move_orig_ids').ids or [])
                for move in self.move_lines
            }
            invoices = self.invoice_ids.filtered(lambda r: r.state in ('draft'))
            del_invoice = self.env['account.move']
            for invoice in invoices:
                for line in invoice.invoice_line_ids:
                    if True in line.mapped('sale_line_ids').mapped('is_delivery'):
                        del_invoice |= invoice
                        line.unlink()

            #cancel the existing DO
            self.with_context(from_reset_picking=True).action_cancel()
            #if the order is in locked state we cannot make any changes so change it to sale.
            previous_state = self.sale_id.state
            self.sale_id.write({'state': 'sale'})
            #create new DO
            for move in self.move_lines:
                move.sale_line_id.with_context({'reset_po_line_id': po_id.get(move.id)})._action_launch_stock_rule()
                new_move  = move.sale_line_id.move_ids.filtered(lambda rec: rec.state not in ('cancel', 'done'))
                if new_move.move_orig_ids.procure_method == 'make_to_stock' and po_id.get(move.id)[1]:
                    new_move.move_orig_ids.write({
                        'procure_method': 'make_to_order',
                        'move_orig_ids': [[6, 0, po_id.get(move.id)[1]]]
                    })
                    new_move._action_assign()
            self.sale_id.write({'state': previous_state})
            for inv in del_invoice:
                delivery_line = self.sale_id.order_line.filtered(lambda r: r.is_delivery)
                for line in delivery_line:
                    vals = delivery_line._prepare_invoice_line()
                    inv.write({'invoice_line_ids': [(0, 0, vals)]})

    def _create_backorder(self):
        res = super()._create_backorder()
        if self.is_create_back_order:
            for picking in res:
                for move in picking.move_lines:
                    if move.location_id.is_transit_location:
                        transit_lines = move.move_orig_ids.filtered(lambda rec: rec.state not in ('done', 'cancel'))
                        if not transit_lines.transit_picking_id:
                            transit_lines.write({'transit_picking_id': move.picking_id.id, 'move_dest_ids': [(6, 0, move.ids)]})
                            transit_lines._action_assign()
        return res

        # if self.state not in ('done', 'in_transit') and 'make_to_order' in self.transit_move_lines.mapped('procure_method'):
        #     for move in self.transit_move_lines:
        #         print(move.move_orig_ids.mapped('state'), move.move_orig_ids)
        #         if self.state not in ('done', 'in_transit') and 'make_to_order' in self.transit_move_lines.mapped('procure_method'):
        #             for move in self.transit_move_lines:
        #                 print(move.move_orig_ids.mapped('state'), move.move_orig_ids)
        #                 if move.move_orig_ids and 'done' not in move.move_orig_ids.mapped('state') or move.created_purchase_line_id:
        #                     line = move.move_dest_ids.mapped('sale_line_id')
        #                     move._action_cancel()
        #                     reset_po_line_id = move.created_purchase_line_id.id
        #                 old_state = line.state
        #                 if line.order_id.state == 'done':
        #                     line.order_id.write({'state': 'sale'})
        #                 line.with_context({'reset_po_line_id': move.created_purchase_line_id.id})._action_launch_stock_rule()
        #                 # if line.state != old_state:
        #                 #     line.state = old_state
        #                 # print(move,line)
        #                 # qty = line._get_qty_procurement(False)
        #                 # group_id = line._get_procurement_group()
        #                 # values = line._prepare_procurement_values(group_id=group_id)
        #                 # procurements = [self.env['procurement.group'].Procurement(
        #                 #     line.product_id, line.product_uom_qty, line.product_uom,
        #                 #     line.order_id.partner_shipping_id.property_stock_customer,
        #                 #     line.name, line.order_id.name, line.order_id.company_id, values)]
        #                 # self.env['procurement.group'].run(procurements)
        #                 # print(line.move_ids, move)
        #                 # if input('choice') == 'y':print(k)

    # @api.model
    # def reset_picking_with_route(self):
    #     picking = self.env['stock.picking'].search(
    #         [('state', 'in', ['confirmed', 'waiting', 'assigned', 'in_transit']), ('batch_id', '!=', False), ('batch_id.state', '=', 'draft')])
    #     picking.mapped('route_id').write({'set_active': False})
    #     # removed newly created batch with empty pciking lines.
    #     picking.mapped('batch_id').sudo().unlink()
    #     return picking.write({'route_id': False})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
