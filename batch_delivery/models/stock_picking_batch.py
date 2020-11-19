# -*- coding: utf-8 -*-

from datetime import date

import werkzeug
from odoo import models, fields, api, _
from odoo.exceptions import UserError


def urlplus(url, params):
    return werkzeug.Href(url)(params or None)


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    route_id = fields.Many2one('truck.route', string='Route', track_visibility='onchange', readonly=True)
    truck_driver_id = fields.Many2one('res.partner', string='Driver', track_visibility='onchange')
    date = fields.Date(string='Scheduled Date', default=date.today())
    payment_ids = fields.One2many('account.payment', 'batch_id', string='Payments')
    actual_returned = fields.Float(string='Actual Amount Returned', help='Actual amount returned by the driver.')
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


    @api.depends('picking_ids.state', 'picking_ids.move_lines.product_id', 'picking_ids.move_lines.quantity_done')
    def _compute_gross_weight_volume(self):
        for batch in self:
            for line in batch.mapped('picking_ids').filtered(lambda rec: rec.state != 'cancel').mapped('move_lines'):
                product_qty = line.quantity_done if line.quantity_done else line.reserved_availability
                batch.total_unit += line.product_uom_qty
                batch.total_volume += line.product_id.volume * product_qty
                batch.total_weight += line.product_id.weight * product_qty



    @api.depends('picking_ids.is_late_order')
    def _compute_late_order(self):
        for rec in self:
            rec.have_late_order = any(rec.picking_ids.mapped('is_late_order'))


    @api.multi
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
                            order_amount += ((line.move_id.sale_line_id.price_total / line.move_id.product_uom_qty) * line.qty_done) if line.qty_done else line.move_id.sale_line_id.price_total
                            if line.move_id.sale_line_id.profit_margin:
                                profit_amount +=((line.move_id.sale_line_id.profit_margin / line.move_id.product_uom_qty) * line.qty_done) if line.qty_done else line.move_id.sale_line_id.profit_margin
                else:
                    for line in picking.move_lines:
                        if line.product_uom_qty:
                            order_amount += ((line.sale_line_id.price_total / line.product_uom_qty) * line.quantity_done)  if line.quantity_done else line.sale_line_id.price_total
                            if line.sale_line_id.profit_margin:
                                profit_amount += ((line.sale_line_id.profit_margin / line.product_uom_qty) * line.quantity_done) if line.quantity_done else line.sale_line_id.profit_margin
            batch.total_amount = order_amount
            batch.total_profit = profit_amount
            batch.profit_percentage = batch.total_profit and (batch.total_profit / batch.total_amount) * 100 or 0

    @api.multi
    @api.depends('actual_returned', 'cash_collected_lines', 'cash_collected_lines.amount')
    def _calculate_pending_amount(self):
        for batch in self:
            real_collected = 0
            for cash_line in batch.cash_collected_lines:
                real_collected += cash_line.amount
            batch.pending_amount = batch.actual_returned - real_collected

    @api.multi
    def name_get(self):
        if 'from_route_picker' in self._context:
            result = []
            for batch in self:
                result.append((batch.id, _('%s (%s)') % (batch.name, batch.date and batch.date or '')))
            return result
        return super(StockPickingBatch, self).name_get()

    @api.multi
    def view_pending_products(self):
        for batch in self:
            self.env['picking.pending.product'].search([('user_id', '=', self.env.uid)]).unlink()

            for product in batch.picking_ids.mapped('move_ids_without_package').mapped('product_id'):
                vals = {
                    'product_id': product.id,
                    'batch_id': batch.id,
                    'user_id': self.env.uid
                }
                self.env['picking.pending.product'].create(vals)
        view_id = self.env.ref('batch_delivery.view_picking_pending_product_tree').id
        res = {
            "type": "ir.actions.act_window",
            "name": "Pending Product",
            "res_model": "picking.pending.product",
            "views": [[view_id, "tree"]],
            "context": {},
            "domain": [('user_id', '=', self.env.uid)],
            "target": "current",
        }
        return res

    @api.multi
    def print_master_pickticket(self):
        self.write({'late_order_print': False})
        return self.env.ref('batch_delivery.report_master_pick_ticket').report_action(self, config=False)

    @api.multi
    def print_master_late_order_pickticket(self):
        self.write({'late_order_print': True})
        return self.env.ref('batch_delivery.report_master_pick_ticket').report_action(self, config=False)

    @api.multi
    def print_product_labels(self):
        return self.env.ref('batch_delivery.batch_product_label_report').report_action(self, config=False)

    @api.multi
    def print_delivery_slip(self):
        return self.env.ref('batch_delivery.batch_deliveryslip_report').report_action(self, config=False)

    @api.multi
    def print_driver_spreadsheet(self):
        return self.env.ref('batch_delivery.batch_driver_report').report_action(self, config=False)

    @api.multi
    def confirm_picking(self):
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
            pickings = batch.picking_ids.filtered(lambda picking: picking.state not in ('cancel'))

            if any(picking.state not in ('assigned', 'in_transit', 'done') for picking in pickings):
                raise UserError(_(
                    'Some pickings are still waiting for goods. Please check or force their availability before setting this batch to done.'))
            # invoice creation from batch procesing
            # move every shipment to transit location(default done state of odoo picking)
            for pick in pickings:
                pick.action_make_transit()
        self.write({'state': 'in_progress'})
        return True

    @api.multi
    def done(self):
        for batch in self:
            res = []
            for picking in batch.picking_ids:
                if picking.state not in ('done', 'cancel'):
                    raise UserError(_('Please Process the delivery order %s to continue.') % (picking.name))
                res.append((0, 0, {'partner_id': picking.partner_id.id}))
                # if picking.state == 'done':
                # picking.deliver_products() # button_validate()
            batch.truck_driver_id.is_driver_available = True
            batch.route_id.set_active = False
            batch.write({'cash_collected_lines': res, 'state': 'done'})
        return True

    @api.multi
    def cancel_picking(self):
        result = super(StockPickingBatch, self).cancel_picking()
        self.mapped('truck_driver_id').write({'is_driver_available': True})
        return result

    @api.multi
    def compute_url(self):
        """
        Compute location URL
        """
        for rec in self:
            partners = rec.picking_ids and rec.picking_ids.mapped('partner_id')
            partners.geo_localize()
            params = {'partner_ids': ','.join(map(str, partners and partners.ids or [])),
                      'partner_url': 'customers'
                      }
        return urlplus('/google_map', params)

    @api.multi
    def view_location_map(self):
        url = self.compute_url()
        return {
            'name': 'Picking Locations',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url or ""
        }

    @api.multi
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

    @api.multi
    def register_payments(self):
        for batch in self:
            if not batch.actual_returned:
                raise UserError(_('Please properly enter the returned amount'))

            if batch.cash_collected_lines and all(l.amount > 0 for l in batch.cash_collected_lines):
                batch.cash_collected_lines.create_payment()
            else:
                raise UserError(_('Please properly enter the cash collected breakup lines.'))
            if batch.pending_amount:
                batch.create_driver_journal()

            batch.is_posted = True

    @api.multi
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


StockPickingBatch()


class CashCollectedLines(models.Model):
    _name = 'cash.collected.lines'
    _description = 'Cash Collected Lines'

    batch_id = fields.Many2one('stock.picking.batch', string='Batch')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    amount = fields.Float(string='Amount Collected')
    communication = fields.Char(string=' Check Number')

    @api.multi
    def create_payment(self):
        cash_journal = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
        payment_method = self.env['account.payment.method'].search(
            [('code', '=', 'manual'), ('payment_type', '=', 'inbound')], limit=1)
        if not cash_journal:
            raise UserError(_(
                'Cash journal not defined! \nPlease create a cash journal in the system to process these transactions.'))
        for line in self:
            if not line.amount:
                continue
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_id': payment_method.id,
                'partner_id': line.partner_id.id,
                'amount': line.amount,
                'journal_id': cash_journal.id,
                'communication': line.communication,
                'batch_id': line.batch_id.id,
            }
            payment = self.env['account.payment'].create(payment_vals)
            payment.post()


CashCollectedLines()
