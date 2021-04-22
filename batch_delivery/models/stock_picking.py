# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    _order = 'release_date, deliver_by'

    truck_driver_id = fields.Many2one('res.partner', string='Truck Driver', copy=False)
    route_id = fields.Many2one('truck.route', string='Truck Route', group_expand='_read_group_route_ids', copy=False)
    is_delivered = fields.Boolean(string='Delivered', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('in_transit', 'In Transit'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")
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
    delivery_move_ids = fields.One2many('stock.move', 'delivery_picking_id', string='Transit Moves')
    delivery_move_line_ids = fields.One2many('stock.move.line', 'delivery_picking_id', string='Transit Move Lines')
    shipping_easiness = fields.Selection([('easy', 'Easy'), ('neutral', 'Neutral'), ('hard', 'Hard')],
                                         string='Easiness Of Shipping')
    is_transit = fields.Boolean(string='Transit', copy=False)
    is_late_order = fields.Boolean(string='Late Order', copy=False)
    reserved_qty = fields.Float('Available Quantity', compute='_compute_available_qty')
    low_qty_alert = fields.Boolean(string="Low Qty", compute='_compute_available_qty')
    sequence = fields.Integer(string='Order')
    is_invoiced = fields.Boolean(string="Invoiced", copy=False)
    invoice_ref = fields.Char(string="Invoice Reference", compute='_compute_invoice_ref')
    invoice_ids = fields.Many2many('account.invoice', compute='_compute_invoice_ids')

    @api.depends('sale_id.invoice_ids')
    def _compute_invoice_ids(self):
        for rec in self:
            rec.invoice_ids = rec.sale_id.invoice_ids

    def _compute_invoice_ref(self):
        for rec in self:
            invoice = rec.sale_id.invoice_ids.filtered(lambda r: rec in r.picking_ids)
            if invoice:
                rec.invoice_ref = invoice[-1].move_name

    @api.depends('move_ids_without_package.reserved_availability')
    def _compute_available_qty(self):
        for pick in self:
            moves = pick.mapped('move_ids_without_package').filtered(lambda move: move.state != 'cancel')
            pick.reserved_qty = sum(moves.mapped('reserved_availability'))
            pick.low_qty_alert = pick.item_count != pick.reserved_qty and pick.state != 'done'

    @api.multi
    def validate_multiple_delivery(self, records):
        for rec in records:
            if rec.state != 'in_transit':
                raise UserError(_(
                    "Some of the selected Delivery order is not in transit state"))
            rec.button_validate()


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.change_delivery_days:
                self.shipping_easiness = self.partner_id.shipping_easiness
            else:
                self.shipping_easiness = self.partner_id.zip_shipping_easiness

    @api.multi
    def _compute_item_count(self):
        for picking in self:
            count = 0
            for line in picking.move_lines:
                count += line.product_uom_qty
            picking.item_count = count

    @api.depends('move_type', 'is_delivered', 'move_lines.state', 'move_lines.picking_id', 'is_transit')
    @api.one
    def _compute_state(self):
        ''' State of a picking depends on the state of its related stock.move
        - Draft: only used for "planned pickings"
        - Waiting: if the picking is not ready to be sent so if
          - (a) no quantity could be reserved at all or if
          - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
        - Waiting another move: if the picking is waiting for another move
        - Ready: if the picking is ready to be sent so if:
          - (a) all quantities are reserved or if
          - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
        - Done: if the picking is done.
        - Cancelled: if the picking is cancelled
        '''
        if not self.move_lines:
            self.state = 'draft'
        elif self.is_transit and not all(move.state in ['cancel', 'done'] for move in self.move_lines):
            self.state = 'in_transit'
        elif any(move.state == 'draft' for move in self.move_lines):  # TDE FIXME: should be all ?
            self.state = 'draft'
        elif all(move.state == 'cancel' for move in self.move_lines):
            self.state = 'cancel'
        elif all(move.state in ['cancel', 'done'] for move in self.move_lines):
            self.state = 'done'
        else:
            relevant_move_state = self.move_lines._get_relevant_state_among_moves()
            if relevant_move_state == 'partially_available':
                self.state = 'assigned'
            else:
                self.state = relevant_move_state

    def action_make_transit(self):
        for pick in self:
            if pick.state not in ['in_transit', 'done']:
                pick.is_transit = True
                pick.move_ids_without_package.write({'is_transit': True})
                for line in pick.move_line_ids:
                    line.qty_done = line.move_id.reserved_availability
                    if line.move_id.sale_line_id:
                        line.move_id.sale_line_id.qty_delivered = line.move_id.sale_line_id.pre_delivered_qty + line.move_id.reserved_availability
                if pick.batch_id:
                    pick.sale_id.write({'delivery_date': pick.batch_id.date})

    @api.model
    def _read_group_route_ids(self, routes, domain, order):
        route_ids = self.env['truck.route'].search([('set_active', '=', True)])
        return route_ids

    @api.multi
    def create_invoice(self):
        for picking in self:
            if not any([line.quantity_done for line in picking.move_ids_without_package]):
                raise UserError(_('Please enter quantities before proceed..'))
            if picking.sale_id.invoice_status == 'no':
                raise UserError(_('Nothing to Invoice..'))
            if picking.sale_id.invoice_status == 'to invoice':
                picking.sale_id.action_invoice_create(final=True)
                picking.is_invoiced = True
            if picking.batch_id:
                invoice = picking.sale_id.invoice_ids.filtered(lambda rec: picking in rec.picking_ids)
                invoice.write({'date_invoice': picking.batch_id.date})
            for inv in picking.sale_id.invoice_ids.filtered(lambda rec: rec.state == 'draft'):
                if not inv.journal_id.sequence_id:
                    raise UserError(_('Please define sequence on the journal related to this invoice.'))
                new_name = inv.journal_id.sequence_id.with_context(ir_sequence_date=inv.date_invoice).next_by_id()
                inv.number = new_name
                inv.move_name = new_name
                picking.invoice_ref = new_name

    @api.multi
    def write(self, vals):
        for picking in self:

            #            in_transit = vals.get('in_transit', False)
            #            if in_transit:
            #                historical_picking = self.env['stock.picking'].search([('route_id', '!=', False), ('state', '=', 'done'), ('picking_type_id.code', '=', 'outgoing'), ('partner_id', '=', picking.partner_id.id)], order='create_date desc', limit=1)

            #                route_id = historical_picking and historical_picking.route_id and historical_picking.route_id.id or False
            #                if route_id:
            #                    vals.update({'route_id': route_id})

            route_id = vals.get('route_id', False)
            if route_id:
                BatchOB = self.env['stock.picking.batch']
                batch = BatchOB.search([('state', '=', 'in_progress'), ('route_id', '=', route_id)], limit=1)
                if batch:
                    picking.action_make_transit()
                elif not batch:
                    batch = BatchOB.search([('state', '=', 'draft'), ('route_id', '=', route_id)], limit=1)

                if batch:
                    # picking.action_make_transit()
                    picking.sale_id.write({'delivery_date': batch.date})
                    if picking.is_invoiced:
                        invoice = picking.sale_id.invoice_ids.filtered(lambda rec: picking in rec.picking_ids)
                        invoice.write({'date_invoice': batch.date})

                if not batch:
                    batch = BatchOB.create({'route_id': route_id})
                # if picking.state not in ('assigned', 'done'):
                #     error = "The requested operation cannot be processed because all quantities are not available for picking %s. Please assign quantities for this picking." %(picking.name)
                #     raise UserError(_(error))
                picking.batch_id = batch

                vals['is_late_order'] = batch.state == 'in_progress'
            if 'route_id' in vals.keys() and not (
                    vals.get('route_id', False)) and picking.batch_id and picking.batch_id.state == 'draft':
                vals.update({'batch_id': False})
        res = super(StockPicking, self).write(vals)
        return res

    @api.multi
    def _compute_show_check_availability(self):
        for picking in self:
            has_moves_to_reserve = any(
                move.state in ('waiting', 'confirmed', 'partially_available', 'in_transit') and
                float_compare(move.product_uom_qty, 0, precision_rounding=move.product_uom.rounding)
                for move in picking.move_lines
            )
            picking.show_check_availability = picking.is_locked and picking.state in (
                'confirmed', 'waiting', 'assigned', 'in_transit') and has_moves_to_reserve

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for pick in self:
            pick.is_transit = False
            pick.move_ids_without_package.write({'is_transit': False})
        return res

    @api.multi
    def action_validate(self):
        result = self.button_validate()
        return result

    @api.multi
    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        self.mapped('move_ids_without_package').write({'is_transit': False})
        self.write({'batch_id': False, 'is_late_order': False})
        return res

    @api.multi
    def action_remove(self):
        result = self.write({'batch_id': False, 'route_id': False, 'is_late_order': False})
        return result

    @api.multi
    def action_print_pick_ticket(self):
        return self.env.ref('batch_delivery.batch_picking_active_report').report_action(self)

    @api.multi
    def action_print_product_label(self):

        return self.env.ref('batch_delivery.product_label_report').report_action(self)

    @api.multi
    def button_validate(self):
        """
        if there are movelines with reserved quantities
        and not validated, automatically validate them.
        """
        self.ensure_one()

        if self.picking_type_id.code == 'outgoing':
            for line in self.move_line_ids:
                if line.lot_id and line.pref_lot_id and line.lot_id != line.pref_lot_id:
                    raise UserError(_(
                        "This Delivery for product %s is supposed to use products from the lot %s please clear the Preferred Lot field to override" % (
                            line.product_id.name, line.pref_lot_id.name)))

            no_quantities_done_lines = self.move_line_ids.filtered(lambda l: l.qty_done == 0.0 and not l.is_transit)
            for line in no_quantities_done_lines:
                if line.move_id and line.move_id.product_uom_qty == line.move_id.reserved_availability:
                    line.qty_done = line.product_uom_qty

        res = super(StockPicking, self).button_validate()
        return res

    @api.model
    def reset_picking_with_route(self):
        picking = self.env['stock.picking'].search(
            [('state', 'in', ['confirmed', 'assigned', 'in_transit']), ('batch_id', '!=', False),
             ('batch_id.state', '=', 'draft')])
        picking.mapped('route_id').write({'set_active': False})
        # removed newly created batch with empty pciking lines.
        picking.mapped('batch_id').sudo().unlink()
        picking.write({'route_id': False})

        return True


StockPicking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
