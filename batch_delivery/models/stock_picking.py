# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning
from odoo.tools import float_compare
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
    # delivery_move_ids = fields.One2many('stock.move', 'delivery_picking_id', string='Transit Moves')
    # delivery_move_line_ids = fields.One2many('stock.move.line', 'delivery_picking_id', string='Transit Move Lines')
    shipping_easiness = fields.Selection([('easy', 'Easy'), ('neutral', 'Neutral'), ('hard', 'Hard')], compute="_compute_shipping_easiness",
                                         string='Easiness Of Shipping')
    is_transit = fields.Boolean(string='Transit', copy=False)
    is_late_order = fields.Boolean(string='Late Order', copy=False)
    reserved_qty = fields.Float('Available Quantity', compute='_compute_available_qty')
    low_qty_alert = fields.Boolean(string="Low Qty", compute='_compute_available_qty')
    sequence = fields.Integer(string='Order', default=1)
    is_invoiced = fields.Boolean(string="Invoiced", compute='_compute_state_flags')
    invoice_ref = fields.Char(string="Invoice Reference", compute='_compute_invoice_ref')
    invoice_ids = fields.Many2many('account.move', compute='_compute_invoice_ids')
    is_return = fields.Boolean(compute='_compute_state_flags')
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", tracking=True)
    batch_id = fields.Many2one(
        'stock.picking.batch', string='Batch Picking', check_company=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Batch associated to this picking', copy=False, tracking=True)
    is_internal_transfer = fields.Boolean(string='Internal transfer')
    transit_date = fields.Date()

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
        release_date = []
        if self.move_lines.mapped('sale_line_id').mapped('order_id'):
            release_date = self.move_lines.mapped('sale_line_id').mapped('order_id').mapped('release_date')
        # elif self.move_lines.mapped('purchase_line_id').mapped('order_id'):
        #     release_date = self.move_lines.mapped('purchase_line_id').mapped('order_id').mapped('release_date')
        if self.move_type == 'direct':
            # if self.rma_id:
            #     self.scheduled_date = fields.Datetime.now()
            # el
            if release_date and any(release_date):
                self.scheduled_date = datetime.combine(min(release_date), datetime.min.time())
            elif self.move_lines.mapped('date_expected'):
                self.scheduled_date = min(self.move_lines.mapped('date_expected'))
            else:
                self.scheduled_date = fields.Datetime.now()
        else:
            # if self.rma_id:
            #     self.scheduled_date = fields.Datetime.now()
            # el
            if release_date and any(release_date):
                self.scheduled_date = datetime.combine(min(release_date), datetime.min.time())
            elif self.move_lines.mapped('date_expected'):
                self.scheduled_date = min(self.move_lines.mapped('date_expected'))
            else:
                self.scheduled_date = fields.Datetime.now()

    @api.depends('sale_id.invoice_status', 'invoice_ids', 'invoice_ids.state')
    def _compute_state_flags(self):
        for pick in self:
            if pick.move_lines.mapped('move_orig_ids').ids:
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

    @api.depends('move_type', 'is_delivered', 'move_lines.picking_id', 'is_transit', 'immediate_transfer', 'move_lines.state',)
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
        #todo donno why this method
        if vals.get('is_internal_transfer'):
            if vals.get('location_dest_id'):
                vals['location_dest_id'] = False
        return super().create(vals)

    def action_generate_backorder_wizard(self):
        """
          Delivery order don't need to create a active back order it is is always cancel back order
          new view added for this
        """
        view = self.env.ref('batch_delivery.view_cancel_back_order_form')
        wiz = self.env['stock.backorder.confirmation'].create({'pick_ids': [(4, p.id) for p in self]})

        code = self.mapped('picking_type_code')
        if isinstance(code, list) and len(code) > 0:
            code = code[0]
        if code != 'incoming':
            return {
                'name': 'Immediate Transfer?',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.backorder.confirmation',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }
        return super().action_generate_backorder_wizard()

    def validate_multiple_delivery(self, records):
        for rec in records:
            if rec.state != 'in_transit' and not rec.purchase_id:
                raise UserError(_(
                    "Some of the selected Delivery order is not in transit state"))
            rec.button_validate()

    def load_products(self):
        pass
        # todo need to migrate
        # res = {}
        # for rec in self:
        #     rec.move_ids_without_package.unlink()
        #     if not rec.location_id:
        #         raise UserError(_(
        #             "Source location should be selected"))
        #     else:
        #         msg = ''
        #         quants = self.env['stock.quant'].search([('location_id', '=', rec.location_id.id)])
        #         quants = quants.filtered(lambda r: r.quantity - r.reserved_quantity > 0)
        #         for quant in quants:
        #             product = quant.mapped('product_id')
        #             qty = quant.quantity - quant.reserved_quantity
        #             if not product.property_stock_location:
        #                 msg += product.default_code and product.default_code or product.name
        #                 msg += ', '
        #                 continue
        #             vals = {'product_id': product.id,
        #                     'picking_id': rec.id,
        #                     'name': product.name,
        #                     'location_id': rec.location_id.id,
        #                     'product_uom': product.uom_id.id,
        #                     'location_dest_id': product.property_stock_location.id,
        #                     'product_uom_qty': qty
        #                     }
        #             self.env['stock.move'].create(vals)
        #         if msg:
        #             msg = 'Stock location not assigned for following Products.' + msg

    def action_make_transit(self):
        for pick in self:
            if pick.state not in ['in_transit', 'done']:
                pick.write({
                    'is_transit': True,
                    'transit_date': fields.Date.context_today(pick)
                })
                pick.move_lines.write({'is_transit': True})
                for line in pick.move_lines:
                    line.quantity_done = line.availability
                    if line.sale_line_id:
                        line.sale_line_id.qty_delivered = line.quantity_done
                if pick.batch_id:
                    pick.sale_id.write({'delivery_date': pick.batch_id.date})

    @api.model
    def default_get(self, default_fields):
        result = super(StockPicking, self).default_get(default_fields)
        if self._context.get('from_internal_transfer_action'):
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'internal'), ('name', '=', 'Internal Transfers')], limit=1)
            if picking_type:
                result['picking_type_id'] = picking_type.id
        return result


    # def action_validate(self):
    #     self.ensure_one()
    #     pass

    def action_validate_internal(self):
        self.ensure_one()
        return self.button_validate()


    #todo need to test
    @api.model
    def _read_group_route_ids(self, routes, domain, order):
        route_ids = self.env['truck.route'].search([('set_active', '=', True)])
        return route_ids

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
                        invoice.write({'date_invoice': batch.date})

                if not batch:
                    batch = self.env['stock.picking.batch'].create({'route_id': route_id})
                picking.batch_id = batch

                vals['is_late_order'] = batch.state == 'in_progress'
            if 'route_id' in vals.keys() and not (
                    vals.get('route_id', False)) and picking.batch_id and picking.batch_id.state == 'draft':
                vals.update({'batch_id': False})
            if 'route_id' in vals.keys() and not vals.get('route_id', False):
                picking.mapped('move_lines').write({'is_transit': False})
                vals.update({'batch_id': False, 'is_late_order': False, 'is_transit': False})
                picking.mapped('sale_id').write({'batch_warning': '', 'state': 'sale'})
        return super().write(vals)

    def action_done(self):
        res = super().action_done()
        for pick in self:
            pick.is_transit = False
            pick.move_lines.write({'is_transit': False})
        for line in self.move_line_ids.filtered(lambda r: r.state == 'done'):
            line.product_onhand_qty = line.product_id.qty_available + line.product_id.transit_qty
        return res

    def check_return_reason(self):
        move_info = self.move_lines.filtered(lambda m: m.quantity_done < m.product_uom_qty and not m.reason_id)
        if move_info:
            default_reason = self.env.ref('batch_delivery.default_stock_picking_return_reason', raise_if_not_found=False)
            if default_reason:
                move_info.write({'reason_id': default_reason.id})
            else:
                product_info = move_info.mapped('product_id')
                if product_info and not all([m.reason_id for m in move_info]):
                    msg = '⚠ 𝐘𝐨𝐮 𝐧𝐞𝐞𝐝 𝐭𝐨 𝐞𝐧𝐭𝐞𝐫 𝐭𝐡𝐞 𝐬𝐭𝐨𝐜𝐤 𝐫𝐞𝐭𝐮𝐫𝐧 𝐫𝐞𝐚𝐬𝐨𝐧 𝐟𝐨𝐫 𝐏𝐫𝐨𝐝𝐮𝐜𝐭 \n'
                    for i, product in enumerate(product_info, 1):
                        msg += '\t\t%d. %s\n' % (i, product.display_name)
                    raise UserError(_(msg))

    #todo don't find the reason
    def action_validate(self):
        self.ensure_one()
        if self.picking_type_id.code == 'outgoing' and self.purchase_id:
            return self.button_validate()
        self.check_return_reason()
        return self.button_validate()

    def action_cancel(self):
        for rec in self:
            if self.mapped('invoice_ids').filtered(lambda r: rec in r.picking_ids and r.state in ['open', 'paid']):
                raise UserError("Cannot perform this action, invoice not in draft state")
            # TODO::should we need to cancel the invoice documents?

            if not self._context.get('back_order_cancel', False):
                self.mapped('invoice_ids').filtered(lambda r: rec in r.picking_ids).sudo().action_cancel()
            else:
                self.mapped('invoice_ids').remove_zero_qty_line()
        res = super(StockPicking, self).action_cancel()
        self.mapped('move_lines').write({'is_transit': False})
        self.write({'batch_id': False, 'is_late_order': False})
        return res

    def action_print_invoice(self):
        invoices = self.mapped('invoice_ids').filtered(lambda r: r.state != 'cancel')
        if not invoices:
            raise UserError(_('Nothing to print.'))

        if self.batch_id and self.batch_id.truck_driver_id and not self.batch_id.truck_driver_id.firstname:
            raise UserError(_('Missing firstname from driver: %s' % self.batch_id.truck_driver_id.name))

        return self.env.ref('batch_delivery.ppt_account_selected_invoices_report').report_action(docids=invoices.ids,
                                                                                                 config=False)

    def action_print_pick_ticket(self):
        return self.env.ref('batch_delivery.batch_picking_active_report').report_action(self)

    def action_print_product_label(self):
        return self.env.ref('batch_delivery.product_label_report').report_action(self)

    def action_remove(self):
        self.mapped('move_lines').write({'is_transit': False})
        return self.write({'batch_id': False, 'route_id': False, 'is_late_order': False, 'is_transit': False})

    def do_print_picking(self):
        self.write({'printed': True})
        return self.env.ref('batch_delivery.batch_picking_active_report').report_action(self)

    def receive_product_in_lines(self):
        for line in self.move_lines:
            if not line.quantity_done and line.state != 'cancel':
                if self.picking_type_code == 'incoming':
                    line.quantity_done = line.product_uom_qty
                elif self.picking_type_code == 'outgoing':
                    line.quantity_done = line.reserved_availability

    #todo not migrated
    # def button_validate(self):
    #     """
    #     if there are movelines with reserved quantities
    #     and not validated, automatically validate them.
    #     """
    #     self.ensure_one()
    #
    #     if self.picking_type_id.code == 'outgoing':
    #         for line in self.move_line_ids:
    #             if line.lot_id and line.pref_lot_id and line.lot_id != line.pref_lot_id:
    #                 raise UserError(_(
    #                     "This Delivery for product %s is supposed to use products from the lot %s please clear the Preferred Lot field to override" % (
    #                         line.product_id.name, line.pref_lot_id.name)))
    #
    #         no_quantities_done_lines = self.move_line_ids.filtered(lambda l: l.qty_done == 0.0 and not l.is_transit)
    #         for line in no_quantities_done_lines:
    #             if line.move_id and line.move_id.product_uom_qty == line.move_id.reserved_availability:
    #                 line.qty_done = line.product_uom_qty
    #
    #     res = super(StockPicking, self).button_validate()
    #     return res
    #
    # @api.model
    # def reset_picking_with_route(self):
    #     picking = self.env['stock.picking'].search(
    #         [('state', 'in', ['confirmed', 'assigned', 'in_transit']), ('batch_id', '!=', False),
    #          ('batch_id.state', '=', 'draft')])
    #     picking.mapped('route_id').write({'set_active': False})
    #     # removed newly created batch with empty pciking lines.
    #     picking.mapped('batch_id').sudo().unlink()
    #     picking.write({'route_id': False})
    #
    #     return True
    #
    # def _check_backorder(self):
    #     """
    #
    #     override to remove canceled movelines
    #
    #     This method will loop over all the move lines of self and
    #     check if creating a backorder is necessary. This method is
    #     called during button_validate if the user has already processed
    #     some quantities and in the immediate transfer wizard that is
    #     displayed if the user has not processed any quantities.
    #
    #     :return: True if a backorder is necessary else False
    #     """
    #     quantity_todo = {}
    #     quantity_done = {}
    #     for move in self.mapped('move_lines').filtered(lambda x: x.state != 'cancel'):
    #         quantity_todo.setdefault(move.product_id.id, 0)
    #         quantity_done.setdefault(move.product_id.id, 0)
    #         quantity_todo[move.product_id.id] += move.product_uom_qty
    #         quantity_done[move.product_id.id] += move.quantity_done
    #     for ops in self.mapped('move_line_ids').filtered(lambda x: x.package_id and not x.product_id and not x.move_id):
    #         for quant in ops.package_id.quant_ids:
    #             quantity_done.setdefault(quant.product_id.id, 0)
    #             quantity_done[quant.product_id.id] += quant.qty
    #     for pack in self.mapped('move_line_ids').filtered(lambda x: x.product_id and not x.move_id):
    #         quantity_done.setdefault(pack.product_id.id, 0)
    #         quantity_done[pack.product_id.id] += pack.product_uom_id._compute_quantity(pack.qty_done,
    #                                                                                    pack.product_id.uom_id)
    #     return any(quantity_done[x] < quantity_todo.get(x, 0) for x in quantity_done)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
