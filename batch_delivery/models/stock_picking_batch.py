# -*- coding: utf-8 -*-

from datetime import date

import werkzeug

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
from odoo.tools import float_round
from odoo.exceptions import ValidationError


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    route_id = fields.Many2one('truck.route', string='Route', tracking=True, readonly=True)
    truck_driver_id = fields.Many2one('res.partner', string='Driver', tracking=True)
    date = fields.Date(string='Scheduled Date', copy=False, tracking=True)
    payment_ids = fields.One2many('account.payment', 'batch_id', string='Payments')
    actual_returned = fields.Float(string='Total Amount', help='Total amount returned by the driver.', digits='Product Price')
    cash_collected_lines = fields.One2many('cash.collected.lines', 'batch_id', string='Cash Collected Breakup')
    is_posted = fields.Boolean(string="Posted")
    pending_amount = fields.Float(string="Difference", compute='_calculate_pending_amount')
    total_amount = fields.Float(string="Total Sale Amount", store=True, compute='_calculate_batch_profit')
    profit_percentage = fields.Float(string="Profit%", store=True, compute='_calculate_batch_profit')
    total_profit = fields.Float(string="Total Profit", store=True, compute='_calculate_batch_profit')
    late_order_print = fields.Boolean(string="Late Order")
    have_late_order = fields.Boolean(compute='_compute_late_order')
    total_volume = fields.Float(string="Total Volume", compute='_compute_gross_weight_volume')
    total_weight = fields.Float(string="Total Weight", compute='_compute_gross_weight_volume')
    total_unit = fields.Float(string="Total Unit", compute='_compute_gross_weight_volume')
    batch_payment_count = fields.Integer(string='Batch Payment', compute='_compute_batch_payment_count')
    to_invoice = fields.Boolean(string='Need Invoice', compute='_compute_to_invoice_state')
    invoice_ids = fields.Many2many('account.move', compute='_compute_invoice_ids')
    show_warning = fields.Boolean(string='Pending Line Warning')
    cash_amount = fields.Float(string='Cash Amount', digits='Product Price', tracking=True)
    cheque_amount = fields.Float(string='Check Amount', digits='Product Price', tracking=True)
    #removed the compute in state
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Running'),
        ('in_truck', 'In Progress'),
        ('done', 'Shipping Done'),
        ('no_payment', 'No Payment'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')], default='draft',
        copy=False, tracking=True, required=True)

    @api.depends('picking_ids', 'picking_ids.move_line_ids', 'picking_ids.move_lines', 'picking_ids.move_lines.state')
    def _compute_move_ids(self):
        for batch in self:
            batch.move_ids = batch.picking_ids.move_lines
            batch.move_line_ids = batch.picking_ids.move_line_ids
            batch.show_check_availability = any(m.state not in ['assigned', 'done'] or m.is_transit is False for m in batch.move_ids)

    @api.depends('picking_ids.invoice_ids')
    def _compute_invoice_ids(self):
        for rec in self:
            rec.invoice_ids = rec.picking_ids.mapped('invoice_ids')

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Invoice'


    @api.constrains('cheque_amount', 'cash_amount', 'actual_returned')
    def check_total_amount(self):

        for batch in self:
            msg = ''
            check_lines = batch.cash_collected_lines.filtered(lambda r:r.payment_method_line_id.code in ('check_printing_in', 'batch_payment'))
            if check_lines and float_round(sum(check_lines.mapped('amount')), precision_digits=2) != float_round(batch.cheque_amount, precision_digits=2):
                msg += 'Check Amount mismatch.\n'
            cash_lines = batch.cash_collected_lines.filtered(lambda r:r.payment_method_line_id.code == 'manual')
            if cash_lines and float_round(sum(cash_lines.mapped('amount')), precision_digits=2) != float_round(batch.cash_amount, precision_digits=2):
                msg += 'Cash Amount mismatch.\n'
            if batch.pending_amount:
                msg += 'Total Amount mismatch.\n'
            if float_round(batch.cheque_amount + batch.cash_amount, precision_digits=2) != float_round(batch.actual_returned, precision_digits=2):
                msg += 'Total amount and sum of Cash,Check does not match.\n'
            if msg:
                raise UserError(msg)

    def _compute_to_invoice_state(self):
        for rec in self:
            rec.to_invoice = not all([pick.is_invoiced for pick in rec.picking_ids])


    @api.depends('payment_ids')
    def _compute_batch_payment_count(self):
        for rec in self:
            rec.batch_payment_count = len(rec.payment_ids.mapped('batch_payment_id'))


    @api.depends('picking_ids', 'picking_ids.state', 'picking_ids.move_lines.product_id', 'picking_ids.move_lines.quantity_done')
    def _compute_gross_weight_volume(self):
        for batch in self:
            batch.total_unit = 0
            batch.total_volume = 0
            batch.total_weight = 0
            for line in batch.mapped('picking_ids').filtered(lambda rec: rec.state != 'cancel').mapped('move_lines'):
                product_qty = line.quantity_done if line.quantity_done else line.reserved_availability
                batch.total_unit += line.product_uom_qty
                batch.total_volume += line.product_id.volume * product_qty
                batch.total_weight += line.product_id.weight * product_qty


    @api.depends('picking_ids.is_late_order')
    def _compute_late_order(self):
        for rec in self:
            rec.have_late_order = any(rec.picking_ids.mapped('is_late_order'))

    @api.depends('picking_ids.move_lines.quantity_done', 'picking_ids.move_line_ids.qty_done')
    def _calculate_batch_profit(self):
        """
        #todo not tested
        compute batch total order amount,
        profit,profit percentage
        """
        for batch in self:
            order_amount = 0
            profit_amount = 0
            for picking in batch.picking_ids:
                if picking.move_line_ids:
                    for line in picking.move_line_ids:
                        if line.move_id.product_uom_qty:
                            order_amount += ((
                                                     line.move_id.sale_line_id.price_total / line.move_id.product_uom_qty) * line.qty_done) if line.qty_done else line.move_id.sale_line_id.price_total
                            if line.move_id.sale_line_id.profit_margin:
                                profit_amount += ((
                                                          line.move_id.sale_line_id.profit_margin / line.move_id.product_uom_qty) * line.qty_done) if line.qty_done else line.move_id.sale_line_id.profit_margin
                else:
                    for line in picking.move_lines:
                        if line.product_uom_qty:
                            order_amount += ((
                                                     line.sale_line_id.price_total / line.product_uom_qty) * line.quantity_done) if line.quantity_done else line.sale_line_id.price_total
                            if line.sale_line_id.profit_margin:
                                profit_amount += ((
                                                          line.sale_line_id.profit_margin / line.product_uom_qty) * line.quantity_done) if line.quantity_done else line.sale_line_id.profit_margin
            batch.total_amount = order_amount
            batch.total_profit = profit_amount
            batch.profit_percentage = batch.total_profit and (batch.total_profit / batch.total_amount) * 100 or 0

    @api.depends('actual_returned', 'cash_collected_lines', 'cash_collected_lines.amount')
    def _calculate_pending_amount(self):
        for batch in self:
            real_collected = 0
            for cash_line in batch.cash_collected_lines:
                real_collected += float_round(cash_line.amount, precision_digits=2)
            batch.pending_amount = float_round(batch.actual_returned - real_collected, precision_digits=2)

    def name_get(self):
        result = []
        if 'from_route_picker' in self._context:
            for batch in self:
                if batch.route_id:
                    result.append((batch.id, _('%s (%s) (%s)') % (
                        batch.name, batch.date and batch.date or '',
                        batch.route_id.name and batch.route_id.name or '')))
                result.append((batch.id, _('%s (%s)') % (batch.name, batch.date and batch.date or '')))
            return result
        for batch in self:
            if batch.route_id:
                result.append(
                    (batch.id, _('%s (%s)') % (batch.name, batch.route_id.name and batch.route_id.name or '')))
            result.append((batch.id, _('%s') % (batch.name)))
        return result

    def view_pending_products(self):
        self.ensure_one()
        pending_view = self.env['pending.product.view'].create({'batch_ids': [(6, 0, self.ids)]})
        return pending_view.generate_move_lines()

    def print_master_pickticket(self):
        self.write({'late_order_print': False})
        return self.env.ref('batch_delivery.report_master_pick_ticket').report_action(self, config=False)

    def print_master_late_order_pickticket(self):
        self.write({'late_order_print': True})
        return self.env.ref('batch_delivery.report_master_pick_ticket').report_action(self, config=False)

    def print_product_labels(self):
        return self.env.ref('batch_delivery.batch_product_label_report').report_action(self, config=False)

    def print_delivery_slip(self):
        return self.env.ref('batch_delivery.batch_deliveryslip_report').report_action(self, config=False)



    def print_invoice_report(self):
        self.ensure_one()
        invoices = self.mapped('invoice_ids').filtered(lambda r: r.state != 'cancel')
        if not invoices:
            raise UserError(_('Nothing to print.'))
        if self.truck_driver_id and not self.truck_driver_id.firstname:
            raise UserError(_('Missing firstname from driver: %s' % self.truck_driver_id.name))
        return self.env.ref('batch_delivery.ppt_account_batch_invoices_report').report_action(self, config=False)

    def print_driver_spreadsheet(self):
        return self.env.ref('batch_delivery.batch_driver_report').report_action(self, config=False)

    def print_picking(self):
        pickings = self.mapped('picking_ids')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref('batch_delivery.batch_picking_all_report').report_action(self)

    def action_confirm(self):
        for batch in self:
            if not batch.truck_driver_id:
                raise UserError(_('Driver should be assigned before confirmation.'))

            if not self.route_id:
                raise UserError(_('Route should be assigned before confirmation.'))
            batch.truck_driver_id.is_driver_available = False
            # fetch all unassigned pickings and try to assign
            unassigned_pickings = batch.mapped('picking_ids').filtered(
                lambda picking: picking.state in ('draft', 'waiting', 'confirmed'))
            for pick in unassigned_pickings:
                pick.action_assign()

            # if atleast one picking not assigned, donot allow to proceed
            pickings = batch.picking_ids.filtered(
                lambda picking: picking.state not in ('cancel', 'waiting', 'confirmed'))

            if any(picking.state not in ('assigned', 'in_transit', 'done') for picking in pickings):
                raise UserError(_(
                    'Some pickings are still waiting for goods. Please check or force their availability before setting this batch to done.'))
            # invoice creation from batch procesing
            # move every shipment to transit location(default done state of odoo picking)
            sale_orders = batch.mapped('picking_ids').mapped('sale_id').filtered(lambda r: r.state != 'done')
            if sale_orders:
                sale_orders.action_done()
            for pick in pickings:
                pick.action_make_transit()
                invoice = pick.sale_id.invoice_ids.filtered(lambda rec: pick in rec.picking_ids)
                if invoice:
                    invoice.write({'date_invoice': pick.batch_id.date})

        self.write({'state': 'in_progress'})
        return True

    def action_done(self):
        for batch in self:
            res = []
            sale_orders = batch.mapped('picking_ids').mapped('sale_id').filtered(lambda r: r.state != 'done')
            if sale_orders:
                sale_orders.action_done()
            for picking in batch.picking_ids.filtered(lambda rec: rec.state not in ['cancel']):
                if picking.sale_id and picking.sale_id.invoice_status == 'to invoice' or not picking.is_invoiced:
                    raise UserError(_('Please create invoices for delivery order %s, to continue.') % (picking.name))
                partner_id = picking.partner_id.id
                if picking.sale_id:
                    partner_id = picking.sale_id.partner_invoice_id.id
                res.append((0, 0, {'partner_id': partner_id, 'sequence': picking.sequence or 0}))
            batch.truck_driver_id.is_driver_available = True
            if batch.route_id:
                batch.route_id.set_active = False
            batch.write({'cash_collected_lines': res, 'state': 'done'})
        return True

    def cancel_picking(self):
        self.mapped('truck_driver_id').write({'is_driver_available': True})
        if self.mapped('route_id').ids:
            self.mapped('route_id').write({'set_active': False})
        self.mapped('picking_ids').write({'batch_id': False, 'route_id': False, 'is_late_order': False})
        return self.write({'state': 'cancel'})

    def set_in_truck(self):
        self.write({'state': 'in_truck', 'date': fields.Date.today()})
        sale_orders = self.mapped('picking_ids').mapped('sale_id')
        if sale_orders:
            sale_orders.write({'batch_warning': 'This order has already been processed for shipment'})
            sale_orders.action_done()

    def set_to_draft(self):
        self.write({'state': 'draft', 'date': False})
        sale_orders = self.mapped('picking_ids').mapped('sale_id')
        if sale_orders:
            sale_orders.write({'batch_warning': '', 'state': 'sale'})



    def view_location_map(self):
        pass


    def action_no_payment(self):
        for batch in self:
            batch.state = 'no_payment'

    def action_to_shipping_done(self):
        for batch in self:
            batch.state = 'done'

    @api.depends('picking_ids.move_lines.quantity_done', 'picking_ids.move_line_ids.qty_done')
    def _calculate_batch_profit(self):
        """
        compute batch total order amount,
        profit,profit percentage
        """
        for batch in self:
            order_amount = 0
            profit_amount = 0
            for picking in batch.picking_ids:
                if picking.move_line_ids:
                    for line in picking.move_line_ids:
                        if line.move_id.product_uom_qty:
                            order_amount += ((
                                                     line.move_id.sale_line_id.price_total / line.move_id.product_uom_qty) * line.qty_done) if line.qty_done else line.move_id.sale_line_id.price_total
                            if line.move_id.sale_line_id.profit_margin:
                                profit_amount += ((
                                                          line.move_id.sale_line_id.profit_margin / line.move_id.product_uom_qty) * line.qty_done) if line.qty_done else line.move_id.sale_line_id.profit_margin
                else:
                    for line in picking.move_lines:
                        if line.product_uom_qty:
                            order_amount += ((
                                                     line.sale_line_id.price_total / line.product_uom_qty) * line.quantity_done) if line.quantity_done else line.sale_line_id.price_total
                            if line.sale_line_id.profit_margin:
                                profit_amount += ((
                                                          line.sale_line_id.profit_margin / line.product_uom_qty) * line.quantity_done) if line.quantity_done else line.sale_line_id.profit_margin
            batch.total_amount = order_amount
            batch.total_profit = profit_amount
            batch.profit_percentage = batch.total_profit and (batch.total_profit / batch.total_amount) * 100 or 0

    def view_invoices(self):
        pickings = self.picking_ids
        invoices = pickings.mapped('invoice_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        # action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        # if len(invoices) > 1:
        #     action['domain'] = [('id', 'in', invoices.ids)]
        # elif len(invoices) == 1:
        #     # action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        #     action['res_id'] = invoices.id
        # else:
        #     action = {'type': 'ir.actions.act_window_close'}
        return action


    def view_payments(self):
        payments = self.payment_ids
        action = self.env.ref('account.action_account_payments').read()[0]
        if len(payments) > 1:
            action['domain'] = [('id', 'in', payments.ids)]
        elif len(payments) == 1:
            action['views'] = [(self.env.ref('account.view_account_payment_form').id, 'form')]
            action['res_id'] = payments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    def create_batch_invoice(self):
        for batch in self:
            batch.picking_ids.create_invoice()


    def view_batch_payments(self):
        self.ensure_one()
        payments = self.payment_ids
        batch_payments = payments.mapped('batch_payment_id')
        action = self.env.ref('account_batch_payment.action_batch_payment_in').read()[0]

        if len(batch_payments) > 1:
            action['domain'] = [('id', 'in', batch_payments.ids)]
        elif len(batch_payments) == 1:
            action['views'] = [(self.env.ref('account_batch_payment.view_batch_payment_form').id, 'form')]
            action['res_id'] = batch_payments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action


    def register_payments(self):
        for batch in self:
            msg = ''
            check_lines = batch.cash_collected_lines.filtered(lambda r:r.payment_method_line_id.code in ('check_printing_in', 'batch_payment'))
            if check_lines and float_round(sum(check_lines.mapped('amount')), precision_digits=2) != float_round(batch.cheque_amount, precision_digits=2):
                msg += 'Check Amount mismatch.\n'
            cash_lines = batch.cash_collected_lines.filtered(lambda r:r.payment_method_line_id.code == 'manual')
            if cash_lines and float_round(sum(cash_lines.mapped('amount')), precision_digits=2) != float_round(batch.cash_amount, precision_digits=2):
                msg += 'Cash Amount mismatch.\n'
            if msg:
                raise UserError(_(msg))
            if float_round(batch.cheque_amount + batch.cash_amount, precision_digits=2) != float_round(batch.actual_returned, precision_digits=2):
                raise UserError(_('Total amount and sum of Cash,Check,Credit Card does not match'))
            if not batch.actual_returned:
                raise UserError(_('Please properly enter the returned amount'))
            if not batch.cash_collected_lines:
                raise UserError(_('Please add cash collected lines before proceeding.'))
            if batch.cash_collected_lines and all(l.amount > 0 for l in batch.cash_collected_lines):
                batch.cash_collected_lines.create_payment()
            else:
                batch.show_warning = True
                return
            if batch.pending_amount:
                batch.create_driver_journal()
            batch.show_warning = False
            batch.is_posted = True
            batch.state = 'paid'


    def create_driver_journal(self):

        company_id = self.env['res.users'].browse(self.env.uid).company_id

        driver_writeoff_account = self.env['account.account'].search(
            [('is_driver_writeoff_account', '=', True),
             ('company_id', '=', company_id.id)], limit=1)
        if not driver_writeoff_account:
            raise UserError(_('Please create a driver writeoff account in the chart of accounts.'))
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash'), ('company_id', '=', company_id.id)], limit=1)

        for batch in self:
            receivable_account = batch.truck_driver_id.property_account_receivable_id
            writeoff_line_dict = {
                'name': batch.pending_amount > 0 and 'Truck Driver Repay' or 'Truck Driver Default',
                'partner_id': batch.truck_driver_id.id,
                'account_id': driver_writeoff_account.id,
                'credit': batch.pending_amount < 0 and abs(batch.pending_amount) or 0.00,
                'debit': batch.pending_amount > 0 and batch.pending_amount or 0.00,
                'date_maturity': fields.Date.today()
            }

            receivable_line_dict = {
                'name': batch.pending_amount > 0 and 'Truck Driver Repay' or 'Truck Driver Default',
                'partner_id': batch.truck_driver_id.id,
                'account_id': receivable_account.id,
                'credit': batch.pending_amount > 0 and batch.pending_amount or 0.00,
                'debit': batch.pending_amount < 0 and abs(batch.pending_amount) or 0.00,
                'date_maturity': fields.Date.today()
            }

            journal_entry_vals = {
                'ref': batch.name,
                'journal_id': cash_journal.id,
                'line_ids': [(0, 0, writeoff_line_dict), (0, 0, receivable_line_dict)],
                'state': 'draft',
            }
            journal_entry = self.env['account.move'].create(journal_entry_vals)
            journal_entry.post()
        return True



class CashCollectedLines(models.Model):
    _name = 'cash.collected.lines'
    _description = 'Cash Collected Lines'

    batch_id = fields.Many2one('stock.picking.batch', string='Batch')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    amount = fields.Float(string='Amount Collected', digits='Product Price')
    communication = fields.Char(string='Memo')
    payment_method_line_id = fields.Many2one('account.payment.method.line', domain=[('payment_type', '=', 'inbound')])
    is_communication = fields.Boolean(string='Is Communication')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['bank', 'cash'])])
    partner_ids = fields.Many2many('res.partner', compute='_compute_partner_ids')
    invoice_id = fields.Many2one('account.move')
    discount = fields.Float(string='Discount(%)')
    sequence = fields.Integer(string='Order')
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line', compute='_compute_available_payment_method_ids')
    billable_partner_ids = fields.Many2many('res.partner', compute='_compute_billable_partner_ids')
    common_batch_id = fields.Many2one('batch.payment.common', string='Batch')
    # {account.journal(7, ): {account.payment.method.line(33, ): [
    #     {'payment_type': 'inbound', 'partner_type': 'customer', 'payment_method_line_id': 33, 'partner_id': 5083,
    #      'amount': 1256.78, 'journal_id': 7, 'communication': False, 'batch_id': 741, 'discount_amount': 0.0,
    #      'discount_journal_id': False},
    #     {'payment_type': 'inbound', 'partner_type': 'customer', 'payment_method_line_id': 33, 'partner_id': 5083,
    #      'amount': 20.0, 'journal_id': 7, 'communication': False, 'batch_id': 741}]}, account.journal(8, ): {
    #     account.payment.method.line(24, ): [
    #         {'payment_type': 'inbound', 'partner_type': 'customer', 'payment_method_line_id': 24, 'partner_id': 5083,
    #          'amount': 100.0, 'journal_id': 8, 'communication': False, 'batch_id': 741}]}}

    @api.depends('batch_id')
    def _compute_billable_partner_ids(self):
        for rec in self:
            partner = self.env['res.partner']
            for sale in rec.batch_id.picking_ids.mapped('sale_id'):
                partner |= sale.partner_id | sale.partner_invoice_id
            rec.billable_partner_ids = partner

    @api.depends('journal_id')
    def _compute_available_payment_method_ids(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines('inbound')
            print(pay.journal_id._get_available_payment_method_lines('inbound'))
            # to_exclude = self._get_payment_method_codes_to_exclude()
            # if to_exclude:
            #     pay.available_payment_method_line_ids = pay.available_payment_method_line_ids.filtered(lambda x: x.code not in to_exclude)

    @api.depends('partner_id')
    def _compute_partner_ids(self):
        for line in self:
            partner = self.env['res.partner']
            picking = line.batch_id.picking_ids.filtered(lambda pick: pick.sale_id.partner_invoice_id.id == line.partner_id.id)
            sale = picking[0].sale_id if picking else False
            if sale:
                partner |= sale.partner_id | sale.partner_invoice_id | sale.partner_shipping_id
            line.partner_ids = partner

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        print(self.invoice_id)
        if self.invoice_id:
            self.amount = self.invoice_id.amount_total
            days = (self.invoice_id.date_invoice - fields.Date.context_today(self)).days
            if abs(days) < self.invoice_id.payment_term_id.due_days:
                self.discount = self.invoice_id.payment_term_id.discount_per
            else:
                self.discount = 0

    @api.onchange('discount', 'invoice_id')
    def onchange_discount(self):
        if self.discount and self.invoice_id:
            self.amount = self.invoice_id.amount_total - (self.invoice_id.amount_total * (self.discount / 100))
        elif self.invoice_id:
            self.amount = self.invoice_id.amount_total
        else:
            self.amount = 0

    @api.onchange('payment_method_line_id')
    def _onchange_payment_method_id(self):
        self.is_communication = self.payment_method_line_id.payment_method_id.code == 'check_printing'

# todo not tested same copy is ther in accounting extension
    def create_payment(self):
        """
        override in accounting extension
        """
        pass
        print('batch delivery')
        batch_payment_info = {}

        for line in self:
            if not line.amount:
                continue

            need_writeoff = True if line.discount else False

            if need_writeoff and not self.env.user.company_id.discount_account_id:
                raise UserError(_('Please set a discount account in company.'))
            if line.invoice_id:
                batch_payment_info.setdefault(line.journal_id, {}). \
                    setdefault(line.payment_method_id, []). \
                    append({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_id': line.payment_method_id.id,
                    'partner_id': line.partner_id.id,
                    'amount': line.amount,
                    'journal_id': line.journal_id.id,
                    'invoice_ids': [(6, 0, line.invoice_id.ids)],
                    'communication': line.communication,
                    'batch_id': line.batch_id.id,
                    'payment_difference_handling': 'reconcile' if need_writeoff else False,
                    'writeoff_label': line.invoice_id.payment_term_id.name if need_writeoff else False,
                    'writeoff_account_id': self.env.user.company_id.discount_account_id.id if need_writeoff else False
                })
                if line.invoice_id:
                    line.invoice_id.write({'discount_from_batch': line.discount})
            else:
                batch_payment_info.setdefault(line.journal_id, {}). \
                    setdefault(line.payment_method_id, []). \
                    append({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_id': line.payment_method_id.id,
                    'partner_id': line.partner_id.id,
                    'amount': line.amount,
                    'journal_id': line.journal_id.id,
                    'communication': line.communication,
                    'batch_id': line.batch_id.id,
                })

        AccountBatchPayment = self.env['account.batch.payment']

        for journal, batch_vals in batch_payment_info.items():
            for payment_method, payment_vals in batch_vals.items():
                ob = AccountBatchPayment.create({
                    'batch_type': 'inbound',
                    'journal_id': journal.id,
                    'payment_ids': [(0, 0, vals) for vals in payment_vals],
                    'payment_method_id': payment_method.id,
                })
                # ob.payment_ids.action_validate_invoice_payment()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
