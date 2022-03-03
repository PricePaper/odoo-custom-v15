# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime, date
from datetime import timedelta
from collections import Counter
import pytz
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_is_zero
from odoo.tools import float_round


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    release_date = fields.Date(string="Earliest Delivery Date", copy=False,
                               default=lambda s: s.get_release_deliver_default_date())
    deliver_by = fields.Date(string="Deliver By", copy=False, default=lambda s: s.get_release_deliver_default_date())
    customer_code = fields.Char(string='Partner Code', related='partner_id.customer_code')
    is_creditexceed = fields.Boolean(string="Credit limit exceeded", default=False, copy=False)
    is_low_price = fields.Boolean(string="Is Low Price", default=False, copy=False)
    credit_warning = fields.Text(string='Credit Limit Warning Message', compute='compute_credit_warning', copy=False)
    low_price_warning = fields.Text(string='Low Price Warning Message', compute='compute_credit_warning', copy=False)
    ready_to_release = fields.Boolean(string="Ready to release credit hold", default=False, copy=False)
    release_price_hold = fields.Boolean(string="Ready to release Price hold", default=False, copy=False)
    gross_profit = fields.Monetary(compute='calculate_gross_profit', string='Predicted Profit')
    is_quotation = fields.Boolean(string="Create as Quotation", default=False, copy=False)
    profit_final = fields.Monetary(string='Profit')
    state = fields.Selection(selection_add=[
        ('waiting', 'Waiting'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('released', 'Released')
    ], string='Status', readonly=True, copy=False, index=True, tracking=True,
        default='draft')
    storage_contract = fields.Boolean(string="Storage Product", default=False, copy=True)
    total_volume = fields.Float(string="Total Order Volume", compute='_compute_total_weight_volume')
    total_weight = fields.Float(string="Total Order Weight", compute='_compute_total_weight_volume')
    total_qty = fields.Float(string="Total Order Quantity", compute='_compute_total_weight_volume')
    sc_po_done = fields.Boolean(copy=False)
    show_contract_line = fields.Boolean(compute='_compute_show_contract_line', store=False)
    hold_state = fields.Selection(
        [('credit_hold', 'Credit Hold'),
         ('price_hold', 'Price hold'),
         ('both_hold', 'Price, Credit Hold'),
         ('release', 'Order Released')],
        string='Hold Status', default=False, copy=False)
    invoice_address_id = fields.Many2one('res.partner', string="Billing Address")
    sc_child_order_count = fields.Integer(compute='_compute_sc_child_order_count')
    delivery_cost = fields.Float(string='Estimated Delivery Cost', readonly=True, copy=False)
    active = fields.Boolean(tracking=True, default=True)
    date_order = fields.Datetime(string='Confirmation Date')

    @api.model
    def get_release_deliver_default_date(self):
        user_tz = self.env.user.tz or "UTC"
        user_time = datetime.now(pytz.timezone(user_tz)).date()
        user_time = user_time + relativedelta(days=1)
        return user_time

    def compute_credit_warning(self):

        for order in self:
            pending_invoices = order.partner_id.invoice_ids.filtered(
                lambda rec: rec.move_type == 'out_invoice' and rec.state == 'posted' and rec.payment_state not in ('paid', 'in_payment') and (
                            rec.invoice_date_due and rec.invoice_date_due < date.today() or not rec.invoice_date_due))

            msg = ''
            msg1 = ''
            invoice_name = []
            for invoice in pending_invoices:
                term_line = invoice.invoice_payment_term_id.line_ids.filtered(lambda r: r.value == 'balance')
                date_due = invoice.invoice_date_due
                if term_line and term_line.grace_period:
                    date_due = date_due + timedelta(days=term_line.grace_period)
                if date_due and date_due < date.today():
                    invoice_name.append(invoice.name)
            if invoice_name:
                msg += 'Customer has pending invoices.\n %s ' % '\n'.join(invoice_name)
            if order.partner_id.credit + order.amount_total > order.partner_id.credit_limit:
                msg += "\nCustomer Credit limit Exceeded.\n %s 's Credit limit is  %.2f  and due amount is %.2f\n" % (
                    order.partner_id.name, order.partner_id.credit_limit,
                    (order.partner_id.credit + order.amount_total))
            for order_line in order.order_line.filtered(lambda r: not r.storage_contract_line_id):
                if order_line.price_unit < order_line.working_cost and not order_line.rebate_contract_id:
                    msg1 += '[%s]%s unit price is less than  product cost price.\n' % (order_line.product_id.default_code, order_line.product_id.name)
            if order.carrier_id and order.gross_profit < order.carrier_id.min_profit:
                msg1 += 'Order profit is less than minimum profit'
            order.credit_warning = msg
            order.low_price_warning = msg1

    def check_credit_limit(self):
        """
        whether the partner's credit limit exceeded or
        partner has pending invoices block the sale order confirmation
        and display warning message.
        """
        for order in self:
            if order.credit_warning:
                order.write({'is_creditexceed': True, 'ready_to_release': False})
                order.message_post(body=order.credit_warning)
                return order.credit_warning
            order.write({'is_creditexceed': False, 'ready_to_release': True})
            return ''

    def check_low_price(self):
        """
        whether order contains low price line
        block the sale order confirmation
        and display warning message.
        """
        self.ensure_one()
        if self.low_price_warning:
            self.write({'is_low_price': True, 'release_price_hold': False})
            self.message_post(body=self.low_price_warning)
            return self.low_price_warning
        self.write({'is_low_price': False, 'release_price_hold': True})
        return ''

    def action_confirm(self):
        """
        create record in price history
        and also update the customer pricelist if needed.
        create invoice for bill_with_goods customers.
        """

        if self._context.get('from_import'):
            return super(SaleOrder, self).action_confirm()
        for order in self:
            if not order.carrier_id:
                raise ValidationError('Delivery method should be set before confirming an order')
            if not any(order_lines.is_delivery for order_lines in order.order_line):
                raise ValidationError('Delivery lines should be added in order lines before confirming an order')
            price_warning = ''
            credit_warning = ''
            if not order.ready_to_release:
                credit_warning = order.check_credit_limit()
                if credit_warning:
                    order.hold_state = 'credit_hold'
            if not order.release_price_hold:
                price_warning = order.check_low_price()
                if price_warning:
                    order.hold_state = 'both_hold'
                    if not credit_warning:
                        order.hold_state = 'price_hold'
            if credit_warning or price_warning:
                view_id = self.env.ref('price_paper.view_sale_warning_wizard').id
                return {
                    'name': 'Warning',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.warning.wizard',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'context': {'default_warning_message': '\n'.join([credit_warning, price_warning])},
                    'target': 'new'
                }
            if order.hold_state in ('credit_hold', 'price_hold', 'both_hold'):
                order.hold_state = 'release'
            sc_line = order.order_line.mapped('storage_contract_line_id')
            sc_not_avl = sc_line.filtered(lambda r: r.storage_remaining_qty <= 0)
            if sc_not_avl:
                raise ValidationError('There is no available quantity in Storage Contract : \n ➤ %s' % ','.join(
                    [name[:-22] for name in sc_not_avl.mapped('display_name')]))

            for line in sc_line:
                qty = sum(line.storage_contract_line_ids.filtered(lambda r: r.id in order.order_line.ids).mapped(
                    'product_uom_qty'))
                if line.storage_remaining_qty < qty:
                    raise ValidationError(
                        'You are planning to sell more than available qty in Storage Contract: \n ➤ {0} \n There is only {1:.2f} left.'.format(
                            line.display_name[:-22], line.storage_remaining_qty))

        res = super(SaleOrder, self).action_confirm()

        for order in self:
            for order_line in order.order_line:
                if order_line.is_delivery:
                    continue
                if not order_line.update_pricelist:
                    continue
                order_line.update_price_list()

        return res

    @api.depends('state', 'order_line.invoice_status', 'order_line.invoice_lines')
    def _get_invoiced(self):
        super(SaleOrder, self)._get_invoiced()
        for order in self:
            if order.storage_contract and order.state in ['done', 'received', 'released']:
                if any([l.invoice_status == 'to invoice' for l in order.order_line if not l.is_downpayment]):
                    order.invoice_status = 'to invoice'
                elif all([l.invoice_status == 'invoiced' for l in order.order_line if not l.is_downpayment]):
                    order.invoice_status = 'invoiced'
                elif all([l.invoice_status == 'upselling' for l in order.order_line if not l.is_downpayment]):
                    order.invoice_status = 'upselling'
                else:
                    order.invoice_status = 'no'

    # todo not needed
    # def _valid_field_parameter(self, field, name):
    #     return name in ['track_visibility', 'track_sequence'] or super()._valid_field_parameter(field, name)

    # todo why excluding sent orders?
    def _compute_sc_child_order_count(self):
        for order in self:
            order.sc_child_order_count = len(order.order_line.mapped('storage_contract_line_ids.order_id').filtered(
                lambda r: r.state not in ['sent', 'cancel']))

    # todo not used anywhere
    # def make_done_orders(self):
    #     # orders = self.env['sale.order'].search([('state', '=', 'sale'), ('invoice_status', '=', 'invoiced')])
    #     for order in self:
    #         picking_status = order.picking_ids.mapped('state')
    #         invoice_state = order.invoice_ids.mapped('state')
    #         if picking_status and any(state not in ('done', 'cancel') for state in picking_status):
    #             continue
    #         if invoice_state and any(state in ('draft') for state in invoice_state):
    #             continue
    #         order.action_done()
    #     return True

    @api.depends('partner_id')
    def _compute_show_contract_line(self):
        for order in self:
            show_contract_line = False
            if order.partner_id:
                sc_order = self.env['sale.order'].with_context(sc=True).search(
                    [('state', '=', 'released'), ('partner_id', '=', order.partner_id.id)])
                count = sc_order.mapped('order_line').filtered(lambda r: r.storage_remaining_qty > 0)
                if len(count) > 0:
                    show_contract_line = True
            order.show_contract_line = show_contract_line

    @api.depends('order_line.product_id', 'order_line.product_uom_qty')
    def _compute_total_weight_volume(self):
        for order in self:
            volume = 0
            weight = 0
            qty = 0
            for line in order.order_line:
                if not line.is_delivery:
                    volume += line.gross_volume
                    weight += line.gross_weight
                    qty += line.product_uom_qty
            order.total_volume = volume
            order.total_weight = weight
            order.total_qty = qty

    def confirm_multiple_orders(self, records):
        msg = ''
        for order in records:
            if order.state != 'draft':
                raise UserError(
                    "Order no %s is in %s state, all orders should be in Draft state" % (order.name, order.state))
            res = order.action_confirm()
            if isinstance(res, dict) and res.get('context', {}).get('warning_message'):
                msg = '%s\n%s - %s' % (msg, order.name, res.get('context').get('warning_message'))
        if msg:
            raise UserError(msg)
        return True

    def activate_views(self):
        except_view = []
        for view in self.env['ir.ui.view'].search([('active', '=', False)]):
            name = ['account_batch_payment_extension', 'odoov12_theme2', 'account_financial_data', 'payment_gateway_ui', 'accounting_extension',
                    'price_maintanance', 'account_partial_payment', 'price_paper', 'purchase_extension', 'audian_theme', 'purge_old_open_credits',
                    'authorize_net_integration', 'quick_create_disable', 'batch_delivery', 'rma_extension', 'crm_enhancements', 'sale_line_reports',
                    'customer_contract', 'saleperson_payment_collection', 'customer_statement_report', 'sales_analysis_report',
                    'deviated_cost_sale_report', 'sales_commission', 'global_price_increase', 'special_item_requests', 'instant_invoice',
                    'stock_orderpoint_enhancements', 'inventory_adjustment_extension', 'stock_product_location', 'inventory_warning',
                    'web_listview_sticky_header', 'kpi_dashboard', 'website_scraping', 'odoo_fbprophet', 'web_widget_color', 'odoov12_theme']
            if view.xml_id.split('.')[0] in name:
                try:
                    view.write({'active': True})
                except Exception as e:
                    except_view.append(view.xml_id)
        import logging
        logging.error('************************************')
        logging.error(except_view)
        return True

    def action_cancel(self):

        # return False
        # todo not finished some confusions in PO relation
        self.ensure_one()
        self.write({
            'is_creditexceed': False,
            'ready_to_release': False,
            'is_low_price': False,
            'release_price_hold': False,
            'hold_state': False
        })
        purchase_order = self._get_purchase_orders()
        if purchase_order.mapped('state') in ['purchase', 'done', 'received']:
            raise UserError('You can not cancel this order since the purchase order is already processed.')
        purchase_order.button_cancel()
        self.order_line.filtered('storage_contract_line_id').write({'product_uom_qty': 0})
        # todo sc things need to check
        # for sale_order in self:
        # else:
        #     sale_order.sudo().order_line.mapped('move_ids.created_purchase_line_id.order_id').button_cancel()
        # if sale_order.storage_contract:
        #     sale_order.order_line.mapped('purchase_line_ids.order_id').button_cancel()
        # else:
        #     for so_line in sale_order.order_line:
        #         for po_line in so_line.mapped('move_ids').filtered(lambda r: r.state != 'cancel').mapped(
        #                 'created_purchase_line_id'):
        #             if po_line.order_id.state in ['purchase', 'done', 'received']:
        #                 raise UserError(_('You cannot cancel this order.'))
        #             else:
        #                 if len(po_line.order_id.origin.split(',')) > 1 or len(
        #                         po_line.order_id.origin.split(', ')) > 1:
        #                     po_line.write({'product_qty': po_line.product_qty - so_line.product_uom_qty})
        #                     po_line.order_id.message_post(body=_(
        #                         "sale order %s has been cancelled by the user %s." % (
        #                             sale_order.name, self.env.user.name)),
        #                         subtype_id=self.env.ref('mail.mt_note').id)
        #                 else:
        #                     po_line.order_id.button_cancel()

        # sc_having_lines = sale_order.order_line.filtered('storage_contract_line_id')
        # if sc_having_lines:
        #     sc_having_lines.write({'product_uom_qty': 0})
        return super(SaleOrder, self).action_cancel()

    # TODO :: FIX THIS FOR ODOO-15 MIGRATION
    # TODO: re-implement for account logic
    def _create_storage_downpayment_invoice(self, order, so_lines):
        pass

    # todo what is the use of it
    def action_create_open_invoice_xmlrpc(self, invoice_date):
        # sale_amount = self.amount_total or 0
        # invoice_amount = round(sum(rec.amount_total_signed for rec in self.invoice_ids) or 0.0, 2)
        # data = {'sale_amount': sale_amount, 'invoice_amount': invoice_amount}
        # if sale_amount == invoice_amount or sale_amount == -invoice_amount:
        #     return self.invoice_ids and self.invoice_ids.ids or False, data
        # else:
        #     self.action_invoice_create(final=True)
        #     self.invoice_ids.write({'move_name': self.note, 'date_invoice': invoice_date or False})
        #     self.invoice_ids.action_invoice_open()
        #     invoice_amount = sum(rec.amount_total for rec in self.invoice_ids) or 0
        #     data = {'sale_amount': sale_amount, 'invoice_amount': invoice_amount}
        #     return self.invoice_ids.ids, data

        data = {'sale_amount': 0.00, 'invoice_amount': 0.00}
        return [], data

    # TODO :: FIX THIS FOR ODOO-15 MIGRATION
    def import_draft_invoice(self, data):

        # if self.invoice_ids:
        #     sale_amount = self.amount_total or 0
        #     invoice_amount = sum(rec.amount_total for rec in self.invoice_ids) or 0
        #     res = {'sale_amount': sale_amount, 'invoice_amount': invoice_amount}
        #     return res
        #
        # missing_msg = ''
        #
        # picking_ids = self.picking_ids
        # move_lines = self.picking_ids.mapped('move_line_ids')
        # picking_ids.is_transit = True
        # picking_ids.move_ids_without_package.write({'is_transit': True})
        # for line in data['do_lines']:
        #     product_id = line.get('product_id')
        #     product_uom_qty = line.get('quantity_ordered')
        #     qty_done = line.get('quantity_shipped')
        #     if qty_done != 0:
        #         move_line = move_lines.filtered(lambda r: r.product_id.id == product_id)
        #         if move_line:
        #             move_line.qty_done = qty_done
        #             move_line.move_id.sale_line_id.qty_delivered = qty_done
        #         else:
        #             missing_msg += 'Invoice : ' + data.get('name') + ' Product_id : ' + str(product_id) + '\n'
        # delivery_line = self.order_line.filtered(lambda r: r.product_id.default_code == 'misc')
        # if delivery_line:
        #     delivery_line.qty_delivered_method = 'manual'
        #     delivery_line.qty_delivered_manual = 1
        # if missing_msg:
        #     return {'missing_msg': missing_msg}
        #
        # res = self.action_invoice_create(final=True)
        # invoice = self.env['account.invoice'].browse(res)
        # invoice.write({'move_name': data.get('name'), 'date_invoice': data.get('date')})
        # picking_ids.write({'is_invoiced': True})
        # sale_amount = self.amount_total or 0
        # invoice_amount = sum(rec.amount_total for rec in self.invoice_ids) or 0
        # res = {'sale_amount': sale_amount, 'invoice_amount': invoice_amount, 'missing_msg': missing_msg}

        res = {'sale_amount': 0.00, 'invoice_amount': 0.00, 'missing_msg': 0.00}
        return res

    def action_create_order_line_xmlrpc(self, vals):
        order_line = self.env['sale.order.line'].create(vals)
        order_line.qty_delivered_method = 'manual'
        order_line.qty_delivered_manual = vals.get('qty_delivered_manual')
        order_line.qty_to_invoice = vals.get('qty_delivered_manual')
        return order_line.id

    def fix_for_do(self):
        self.action_cancel()
        self.action_draft()
        self.action_confirm()
        return True

    # todo above methods are not used

    def run_storage(self):
        # logic is wrong it is creating stock moves fro SC main order
        # create PO directly
        for order in self:
            route = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=True)
            so_lines = order.order_line.filtered(
                lambda r: r.product_id.type != 'service' and not r.display_type and not r.is_downpayment)
            so_lines.write({'route_id': route.id, 'state': 'sale'})
            errors = []
            order.order_line._action_launch_stock_rule()
            for line in so_lines:
                line.move_ids.created_purchase_line_id.write({'sale_line_id': line.id})
            order.write({'state': 'waiting'})
            # service line update
            purchase_orders = order._get_purchase_orders().filtered(lambda rec: rec.state == 'draft')

            for service_line in order.order_line.filtered(
                    lambda r: r.product_id.type == 'service' and not r.display_type and not r.is_downpayment):
                for po in purchase_orders:
                    product_taxes = service_line.product_id.supplier_taxes_id.filtered(
                        lambda x: x.company_id.id == po.company_id.id)
                    taxes = po.fiscal_position_id.map_tax(product_taxes)
                    price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(
                        service_line.price_unit,
                        service_line.product_id.supplier_taxes_id,
                        taxes,
                        self.company_id
                    )
                    if po.currency_id and po.partner_id.currency_id != po.currency_id:
                        price_unit = po.partner_id.currency_id.compute(price_unit, po.currency_id)
                    purchase_qty_uom = service_line.product_uom._compute_quantity(service_line.product_uom_qty,
                                                                                  service_line.product_id.uom_po_id)
                    self.env['purchase.order.line'].create({
                        'name': service_line.name,
                        'product_qty': purchase_qty_uom,
                        'product_id': service_line.product_id.id,
                        'product_uom': service_line.product_id.uom_po_id.id,
                        'price_unit': price_unit,
                        'date_planned': po.date_planned,
                        'taxes_id': [(6, 0, taxes.ids)],
                        'order_id': po.id,
                        'sale_line_id': service_line.id,
                    })
            if purchase_orders:
                order.message_post(body='PO Created by : %s' % self.env.user.name)
        return True

    def action_create_storage_do(self):
        """
        create purchase order for storage contract
        """
        self.run_storage()
        self.write({'sc_po_done': True})

    def action_release(self):
        self.write({'state': 'released'})

    def action_restore(self):
        for sc in self:
            orders = sc.order_line.mapped('storage_contract_line_ids.order_id')
            if any([order.state != 'cancel' for order in orders]):
                raise ValidationError(
                    'Cannot UnRelease contract with active sale orders %s' % (', '.join(orders.mapped('name'))))
        return self.write({'state': 'done'})

    @api.depends('picking_policy', 'order_line.customer_lead', 'date_order', 'order_line.state')
    def _compute_expected_date(self):
        for order in self:
            dates_list = []
            confirm_date = fields.Datetime.from_string((order.date_order or order.write_date) if order.state in (
                'sale', 'done') else fields.Datetime.now())
            for line in order.order_line.filtered(lambda x: x.state != 'cancel' and not x._is_delivery()):
                dt = confirm_date + timedelta(days=line.customer_lead or 0.0)
                dates_list.append(dt)
            if dates_list:
                expected_date = min(dates_list) if order.picking_policy == 'direct' else max(dates_list)
                order.expected_date = fields.Datetime.to_string(expected_date)
            else:
                super(SaleOrder, self)._compute_expected_date()

    def action_fax_send(self):
        """
        This function opens a window to compose an email, with the edi sale template message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('price_paper.fax_template_edi_sale')
        if not self.partner_id.fax_number:
            raise ValidationError('Please enter customer Fax number first.')
        email_context = self.env.context.copy()
        email_context.update({
            'email_to': self.partner_id.fax_number + '@efaxsend.com',
            'recipient_ids': ''
        })
        return template.with_context(email_context).send_mail(self.id)

    @api.onchange('partner_shipping_id')
    def onchange_partner_id_carrier_id(self):
        if self.partner_shipping_id:
            shipping_date = date.today() + relativedelta(days=1)
            day_list = []
            if self.partner_shipping_id.change_delivery_days:
                if self.partner_shipping_id.delivery_day_mon:
                    day_list.append(0)
                if self.partner_shipping_id.delivery_day_tue:
                    day_list.append(1)
                if self.partner_shipping_id.delivery_day_wed:
                    day_list.append(2)
                if self.partner_shipping_id.delivery_day_thu:
                    day_list.append(3)
                if self.partner_shipping_id.delivery_day_fri:
                    day_list.append(4)
                if self.partner_shipping_id.delivery_day_sat:
                    day_list.append(5)
                if self.partner_shipping_id.delivery_day_sun:
                    day_list.append(6)
            else:
                if self.partner_shipping_id.zip_delivery_id:
                    if self.partner_shipping_id.zip_delivery_day_mon:
                        day_list.append(0)
                    if self.partner_shipping_id.zip_delivery_day_tue:
                        day_list.append(1)
                    if self.partner_shipping_id.zip_delivery_day_wed:
                        day_list.append(2)
                    if self.partner_shipping_id.zip_delivery_day_thu:
                        day_list.append(3)
                    if self.partner_shipping_id.zip_delivery_day_fri:
                        day_list.append(4)
                    if self.partner_shipping_id.zip_delivery_day_sat:
                        day_list.append(5)
                    if self.partner_shipping_id.zip_delivery_day_sun:
                        day_list.append(6)
            weekday = date.today().weekday()
            day_diff = 0
            if day_list:
                if any(weekday < i for i in day_list):
                    for i in day_list:
                        if weekday < i:
                            day_diff = i - weekday
                            break
                else:
                    day_diff = (6 - weekday) + day_list[0] + 1
                shipping_date = date.today() + relativedelta(days=day_diff)
            self.release_date = shipping_date
            self.deliver_by = shipping_date
            # todo carrier is not updating if user is not using the add wizard
            # self.carrier_id = self.partner_shipping_id.property_delivery_carrier_id
        # else:
        # self.carrier_id = self.partner_id and self.partner_id.property_delivery_carrier_id or False

    # @api.onchange('carrier_id', 'order_line')
    # def onchange_delivery_carrier_method(self):
    #     """ onchange delivery carrier,
    #         recompute the delicery price
    #     """
    #     if self.carrier_id:
    #         self.get_delivery_price()

    @api.model
    def create(self, vals):
        if vals.get('storage_contract'):
            sequence = self.env.ref('price_paper.seq_sc_sale_order', raise_if_not_found=False)
            if sequence:
                vals['name'] = sequence._next()
        order = super(SaleOrder, self).create(vals)
        if order.sales_person_ids:
            order.message_subscribe(partner_ids=order.sales_person_ids.ids)
        return order

    def write(self, vals):
        """
        auto save the delivery line.
        """
        amount = {}
        for order in self:
            if order.state == 'sale':
                amount[order.id] = order.amount_total
        res = super(SaleOrder, self).write(vals)
        for order in self:
            if order.id in amount and amount[order.id] < order.amount_total:
                if order.partner_id.credit + order.amount_total > order.partner_id.credit_limit:
                    if order.picking_ids.filtered(lambda r: r.state == 'in_transit'):
                        raise UserError('You can not add product to a Order which has a DO in transit state')
                    order.action_cancel()
                    order.action_draft()
                    order.action_confirm()

        if not self._context.get('from_import'):
            self.check_payment_term()
        if 'sales_person_ids' in vals and vals['sales_person_ids']:
            self.message_subscribe(partner_ids=vals['sales_person_ids'][0][-1])
        return res

    def copy(self, default=None):
        # ctx = dict(self.env.context)
        # self = self.with_context(ctx)
        new_so = super(SaleOrder, self).copy(default=default)
        for line in new_so.order_line:
            if line.is_delivery:
                line.product_uom_qty = 1
        return new_so

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        records = super(SaleOrder, self).search(args, offset, limit, order, count)
        user = self.env.user
        if self._context.get('sc'):
            return records
        if self._context.get('my_draft') or self._context.get('my_orders'):
            return records.filtered(lambda s: s.user_id == user or user.partner_id in s.sales_person_ids)
        return records

    def get_delivery_price_not_used(self):
        """
        overriden to bypass the delivery price get block for confirmed orders
        """
        for order in self.filtered(lambda o: o.state in ('draft', 'sent', 'sale') and len(o.order_line) > 0):
            # or on an SO that has no lines yet
            order.delivery_rating_success = False
            res = order.carrier_id.rate_shipment(order)
            if res['success']:
                order.delivery_rating_success = True
                order.delivery_price = res['price']
                order.delivery_message = res['warning_message']
                if order.carrier_id.delivery_type not in ['fixed', 'base_on_rule']:
                    order.delivery_cost = res['cost']
            else:
                order.delivery_rating_success = False
                order.delivery_price = 0.0
                order.delivery_message = res['error_message']
                if order.carrier_id.delivery_type not in ['fixed', 'base_on_rule']:
                    order.delivery_cost = 0.0

    def adjust_delivery_line(self):
        """
        method written to adjust delivery charges line in order line
        upon form save with changes in delivery method in sale order record
        """
        res = self.carrier_id.rate_shipment(self)
        price_unit = res.get('price', 0)
        if price_unit != self._get_delivery_line_price() or not self._get_delivery_line_price():
            self._remove_delivery_line()
            self._create_delivery_line(self.carrier_id, price_unit)

        return True

    def _get_delivery_line_price(self):
        return sum(self.env['sale.order.line'].search([('order_id', 'in', self.ids), ('is_delivery', '=', True)]).mapped('price_subtotal')) or 0

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            addr = self.partner_id.address_get(['delivery', 'invoice'])
            self.partner_invoice_id = self.partner_id.id
            self.invoice_address_id = addr['invoice']
            shipping_addr = self.partner_id.child_ids.filtered(
                lambda rec: rec.type == 'delivery' and rec.default_shipping == True)
            if shipping_addr:
                self.partner_shipping_id = shipping_addr.id
            else:
                self.partner_shipping_id = self.partner_id.id
        else:
            self.invoice_address_id = False
        return res

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['invoice_address_id'] = self.invoice_address_id.id
        return invoice_vals

    @api.depends('order_line.profit_margin')
    def calculate_gross_profit(self):
        """
        Compute the gross profit of the SO.
        """

        for order in self:
            gross_profit = sum([line.profit_margin for line in order.order_line])
            # TODO:: remove payment method field from sales_commission.
            if order.partner_id.payment_method == 'credit_card':
                gross_profit -= order.amount_total * 0.03
            # TODO:: remove discount_per,code,oder_type,due_date,is_discount,discount_per field from purchase_extension.
            if order.payment_term_id.discount_per > 0:
                gross_profit -= order.amount_total * (order.payment_term_id.discount_per / 100)
            order.update({'gross_profit': round(gross_profit, 2)})

    @api.constrains('release_date', 'deliver_by')
    def get_release_date_warning(self):

        if not self.release_date:
            self.release_date = date.today() + timedelta(days=1)
        if not self.deliver_by:
            self.deliver_by = date.today() + timedelta(days=1)

        if self.release_date and self.release_date < date.today():
            raise ValidationError('Earliest Delivery Date should be greater than Current Date')

    @api.onchange('release_date')
    def onchange_release_date_warning(self):
        if self.release_date and self.release_date > date.today() + timedelta(days=+6):
            return {'warning': {'title': 'Warning', 'message': 'Earliest Delivery Date is greater than 1 week'}}

    def action_release_credit_hold(self):
        """
        release hold sale order for credit limit exceed.
        """
        for order in self:
            order.write({'is_creditexceed': False, 'ready_to_release': True})
            order.message_post(body="Credit Team Approved")
            if order.release_price_hold:
                order.hold_state = 'release'
                order.action_confirm()
            else:
                order.hold_state = 'price_hold'

    def action_release_price_hold(self):
        """
        release hold sale order for low price.
        """
        for order in self:
            order.write({'is_low_price': False, 'release_price_hold': True})
            order.message_post(body="Sale Team Approved")
            if order.ready_to_release:
                order.hold_state = 'release'
                order.action_confirm()
            else:
                order.hold_state = 'credit_hold'

    # TODO :: odoo default will do this
    # def action_view_purchase(self):
    #     action = self.env.ref('purchase.purchase_rfq').read()[0]
    #     action['domain'] = [('id', 'in', self.mapped('order_line.purchase_line_ids.order_id').ids)]
    #     action.pop('context')
    #     return action

    @api.onchange('payment_term_id')
    def onchange_payment_term(self):
        user = self.env.user
        for order in self:
            partner_payment_term = order.partner_id and order.partner_id.property_payment_term_id
            if (order.payment_term_id.id != partner_payment_term.id) and not user.has_group(
                    'account.group_account_manager'):
                order.payment_term_id = partner_payment_term.id
                return {'warning': {'title': 'Invalid Action!',
                                    'message': "You dont have the rights to change the payment terms of this customer."}}

    def check_payment_term(self):
        """
        Can only proceed with order if payment term is set
        """
        user = self.env.user
        for order in self:
            if not order.payment_term_id:
                raise ValidationError('Payment term is not set for this order please set to proceed.')

    # todo check for unlock
    def action_unlock(self):
        self.filtered(lambda s: s.storage_contract and s.state == 'done').write({'state': 'received'})
        self.filtered(lambda s: not s.storage_contract and s.state == 'done').write({'state': 'sale'})

    def import_action_confirm(self):
        self = self.with_context({'from_import': True})
        return self.action_confirm()

    def view_sc_child_orders(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        if action:
            ids = self.order_line.mapped('storage_contract_line_ids.order_id').ids
            action.update({
                'domain': [
                    ('id', 'in', ids),
                    ('state', 'not in', ('cancel')),
                    ('storage_contract', '=', False)]
            })
            return action

    def add_purchase_history_to_so_line(self):
        """
        Return 'add purchase history to so wizard'
        """
        view_id = self.env.ref('price_paper.view_purchase_history_add_so_wiz').id
        products = self.order_line.mapped('product_id').ids
        sales_history = self.env['sale.history'].search(
            ['|', ('active', '=', False), ('active', '=', True), ('partner_id', '=', self.partner_id.id),
             ('product_id', 'not in', products), ('product_id', '!=', False)]).filtered(
            lambda r: not r.product_id.categ_id.is_storage_contract)
        # addons product filtering
        addons_products = sales_history.mapped('product_id').filtered(lambda rec: rec.need_sub_product).mapped(
            'product_addons_list')
        if addons_products:
            sales_history = sales_history.filtered(lambda rec: rec.product_id not in addons_products)

        search_products = sales_history.mapped('product_id').ids
        context = {
            'default_sale_history_ids': [(6, 0, sales_history.ids)],
            'products': search_products
        }

        return {
            'name': _('%s' % self.partner_id.display_name + ' #' + self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.purchase.history.so',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }

    def action_storage_contract_confirm(self):
        self.write({'state': 'sale', 'date_order': fields.Datetime.today()})
        return True

    def so_duplicate(self):
        new_records = self.env['sale.order']
        for rec in self:
            new_records |= rec.copy()
        action_rec = self.env.ref('sale.action_quotations_with_onboarding')
        action = action_rec.read()[0]
        if len(new_records) > 1:
            action['domain'] = [('id', 'in', new_records.ids)]
        elif len(new_records) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = new_records.ids[0]
        return action

    @api.model
    def sc_archive_cron(self):
        records = self.env['sale.order'].search(
            [('active', '=', True), ('storage_contract', '=', True), ('state', 'in', ['released', 'done'])])
        for record in records:
            if not any(record.order_line.mapped(lambda l: l.storage_remaining_qty)):
                record.write({'active': False})


SaleOrder()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    profit_margin = fields.Monetary(compute='calculate_profit_margin', string="Profit")
    price_from = fields.Many2one('customer.product.price', string='Product Pricelist')
    last_sale = fields.Text(string='Last sale details')
    product_onhand = fields.Float(string='Product Qty Available', compute='compute_available_qty', store=False,
                                  digits='Product Unit of Measure')
    new_product = fields.Boolean(string='New Product', copy=False)
    manual_price = fields.Boolean(string='Manual Price Change', copy=False)
    is_last = fields.Boolean(string='Is last Purchase', copy=False)
    shipping_id = fields.Many2one(related='order_id.partner_shipping_id', string='Shipping Address')
    note = fields.Text('Note')
    note_type = fields.Selection(string='Note Type',
                                 selection=[('permanant', 'Save note'), ('temporary', 'Temporary Note')],
                                 default='temporary')
    confirmation_date = fields.Datetime(related='order_id.date_order', string='Confirmation Date')
    price_lock = fields.Boolean(related='price_from.price_lock', readonly=True)

    # comment the below 2 lines while running sale order line import scripts
    lst_price = fields.Float(string='Standard Price', digits='Product Price', store=True,
                             compute='_compute_lst_cost_prices')
    working_cost = fields.Float(string='Working Cost', digits='Product Price', store=True,
                                compute='_compute_lst_cost_prices')

    # Uncomment the below 2 lines while running sale order line import scripts
    # lst_price = fields.Float(string='Standard Price', digits='Product Price')
    # working_cost = fields.Float(string='Working Cost', digits='Product Price')
    gross_volume = fields.Float(string="Gross Volume", compute='_compute_gross_weight_volume')
    gross_weight = fields.Float(string="Gross Weight", compute='_compute_gross_weight_volume')
    is_addon = fields.Boolean(string='Is Addon')
    update_pricelist = fields.Boolean(string="Update Pricelist", default=True, copy=False)
    remaining_qty = fields.Float(string="Remaining Quantity", compute='_compute_remaining_qty')
    similar_product_price = fields.Html(string='Similar Product Prices')
    sale_uom_ids = fields.Many2many('uom.uom', compute='_compute_sale_uom_ids')
    storage_remaining_qty = fields.Float(string="Remaining qty", compute='_compute_storage_delivered_qty',
                                         search='_search_storage_remaining_qty')
    storage_contract_line_id = fields.Many2one('sale.order.line', string='Contract Line')
    storage_contract_line_ids = fields.One2many('sale.order.line', 'storage_contract_line_id')
    selling_min_qty = fields.Float(string="Minimum Qty")
    note_expiry_date = fields.Date('Note Valid Upto')
    scraped_qty = fields.Float(compute='_compute_scrape_qty', string='Quantity Scraped', store=False)
    date_planned = fields.Date(related='order_id.release_date', store=False, readonly=True, string='Date Planned')

    @api.depends('product_id', 'product_uom_qty', 'price_unit', 'order_id.delivery_cost')
    def calculate_profit_margin(self):
        """
        Calculate profit margin for SO line
        """
        for line in self:
            if line.product_id:
                if line.is_delivery or line.is_downpayment or line.storage_contract_line_id:
                    line.profit_margin = 0.0
                    if line.is_delivery and line.order_id.carrier_id:
                        price_unit = line.order_id.carrier_id.average_company_cost
                        if line.order_id.carrier_id.delivery_type not in ['fixed', 'base_on_rule']:
                            price_unit = line.order_id.delivery_cost
                        line.profit_margin = line.price_subtotal - price_unit
                else:
                    product_price = line.working_cost or 0
                    line_price = line.price_unit
                    if line.product_id.uom_id == line.product_uom and line.product_uom_qty % 1 != 0.0:
                        numer = line.price_unit * line.product_uom_qty
                        denom = (int(line.product_uom_qty / 1.0) + ((line.product_uom_qty % 1) * (
                                100 + line.product_id.categ_id.repacking_upcharge) / 100))
                        line_price = numer / denom
                    line.profit_margin = float_round((line_price - product_price) * line.product_uom_qty,
                                                     precision_digits=2)
            else:
                line.profit_margin = 0.0

    @api.depends('move_ids.picking_id.move_lines.scrapped')
    def _compute_scrape_qty(self):
        for so_line in self:
            so_line.scraped_qty = sum(so_line.move_ids.mapped('picking_id').mapped('move_lines').filtered(
                lambda r: r.scrapped and r.product_id.id == so_line.product_id.id).mapped('quantity_done'))

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced',
                 'order_id.storage_contract')
    def _compute_invoice_status(self):
        super(SaleOrderLine, self)._compute_invoice_status()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.order_id.storage_contract:
                if float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                    line.invoice_status = 'invoiced'
                elif float_compare(line.qty_delivered, line.product_uom_qty,
                                   precision_digits=precision) <= 0 and line.state in ['received', 'done']:
                    line.invoice_status = 'to invoice'
                elif float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                    line.invoice_status = 'upselling'
                else:
                    line.invoice_status = 'no'
            else:
                break

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        super(SaleOrderLine, self)._get_to_invoice_qty()
        for line in self:
            if line.order_id.storage_contract and line.order_id.state in ['done', 'received', 'released']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = (line.product_uom_qty if not line.is_downpayment else 0) - line.qty_invoiced
                else:
                    line.qty_to_invoice = (line.qty_delivered if not line.is_downpayment else 0) - line.qty_invoiced
            else:
                break

    # TODO is_transit is in batch delivery module === dp that's fine
    @api.depends('qty_delivered_method', 'qty_delivered_manual', 'analytic_line_ids.so_line',
                 'analytic_line_ids.unit_amount', 'analytic_line_ids.product_uom_id')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for line in self:
            if line.order_id.storage_contract:
                qty = 0.0
                for po_line in line.sudo().purchase_line_ids:
                    if po_line.state in ('purchase', 'done', 'received'):
                        qty += sum(po_line.move_ids.filtered(lambda s: s.state != 'cancel').mapped('quantity_done'))
                line.qty_delivered = qty
            # else:
            #     if line.qty_delivered_method == 'stock_move':
            #         qty = 0.0
            #         # todo is transit is not available
            #         for move in line.move_ids.filtered(lambda r: r.state == 'done' or r.is_transit is True and not r.scrapped and line.product_id == r.product_id):
            #             if move.location_dest_id.usage == "customer":
            #                 if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
            #                     qty += move.product_uom._compute_quantity(
            #                         move.quantity_done or move.reserved_availability, line.product_uom)
            #             elif move.location_dest_id.usage != "customer" and move.to_refund:
            #                 qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
            #         line.qty_delivered = qty

    @api.depends('product_id.qty_available', 'product_id.outgoing_qty')
    def compute_available_qty(self):
        for line in self:
            if line.product_id:
                line.product_onhand = line.product_id.qty_available - line.product_id.outgoing_qty
            else:
                line.product_onhand = 0.00

    @api.depends('product_uom_qty', 'qty_delivered', 'storage_contract_line_ids.qty_delivered', 'state')
    def _compute_storage_delivered_qty(self):
        for line in self:
            if line.order_id.storage_contract:
                sale_lines = line.storage_contract_line_ids.filtered(
                    lambda r: r.order_id.state not in ['draft', 'cancel'])
                if not line.sudo().purchase_line_ids and line.state in ['released', 'done']:
                    line.storage_remaining_qty = line.product_uom_qty - sum(sale_lines.mapped('qty_delivered')) - sum(
                        sale_lines.mapped('scraped_qty'))
                else:
                    line.storage_remaining_qty = line.qty_delivered - sum(sale_lines.mapped('qty_delivered')) - sum(
                        sale_lines.mapped('scraped_qty'))
            else:
                line.storage_remaining_qty = 0

    @api.model
    def _search_storage_remaining_qty(self, operator, value):
        ids = []
        if operator == '>':
            order_lines = self.env['sale.order.line'].search([
                ('product_id.type', '!=', 'service'),
                ('order_id.storage_contract', '=', True),
                ('state', '=', 'released'),
                ('is_downpayment', '=', False)
            ])
            for sl in order_lines:
                lines = sl.storage_contract_line_ids.filtered(lambda r: r.order_id.state not in ['draft', 'cancel'])
                if not sl.sudo().purchase_line_ids:
                    if (sl.product_uom_qty - sum(lines.mapped('qty_delivered')) - sum(
                            lines.mapped('scraped_qty'))) > value:
                        ids.append(sl.id)
                else:
                    if (sl.qty_delivered - sum(lines.mapped('qty_delivered')) - sum(
                            lines.mapped('scraped_qty'))) > value:
                        ids.append(sl.id)
        return [('id', 'in', ids)]

    @api.depends('product_id.sale_uoms')
    def _compute_sale_uom_ids(self):
        for rec in self:
            if rec.product_id:
                rec.sale_uom_ids = rec.product_id.sale_uoms
            else:
                rec.sale_uom_ids = False

    def product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            # TODO::fix this this field is not available in odoo-15, field removed from sale_stock (12).
            # self.product_packaging = False
            return {}
        if self.product_id.type == 'product' and self.is_mto is False:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.qty_available - product.outgoing_qty, product_qty,
                             precision_digits=precision) == -1:
                is_available = self.is_mto
                if not is_available:
                    message = _('You plan to sell %.2f %s of %s but you only have %.2f %s available in %s warehouse.') % \
                              (self.product_uom_qty, self.product_uom.name, self.product_id.name,
                               product.qty_available - product.outgoing_qty, product.uom_id.name,
                               self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.qty_available - product.outgoing_qty,
                                     self.product_id.qty_available - self.product_id.outgoing_qty,
                                     precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available across all warehouses.\n\n') % \
                                   (self.product_id.qty_available - self.product_id.outgoing_qty, product.uom_id.name)
                        for warehouse in self.env['stock.warehouse'].search([]):
                            quantity = self.product_id.with_context(
                                warehouse=warehouse.id).qty_available - self.product_id.with_context(
                                warehouse=warehouse.id).outgoing_qty
                            if quantity > 0:
                                message += "%s: %s %s\n" % (warehouse.name, quantity, self.product_id.uom_id.name)
                    warning_mess = {
                        'title': 'Not enough inventory!',
                        'message': message
                    }
                    return {'warning': warning_mess}
        return {}

    @api.onchange('tax_id')
    def _onchange_tax(self):
        if not self.tax_id:
            if self.product_id and self.order_id and self.order_id.partner_id \
                    and not self.order_id.partner_id.vat:
                raise UserError('You can not remove Tax for this Partner.')

    # todo replaced with is_mto compute feild
    # def _check_routing(self):
    #     return {}

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        res = self.product_id_check_availability()
        if self.product_id and self.product_uom_qty and self.product_uom:
            if self.product_id.type == 'product':
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                product = self.product_id.with_context(
                    warehouse=self.order_id.warehouse_id.id,
                    lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
                )
                product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
                if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                    is_available = self.is_mto
                    if not is_available:
                        products = product.same_product_ids + product.same_product_rel_ids
                        if not products:
                            self.similar_product_price = False
                            return res
                        similar_product_price = "<table style='width:400px'>\
                                                <tr><th>Alternative Products</th><th>Price</th><th>UOM</th></tr>"
                        product_unit_price = self.price_unit / self.product_uom.factor_inv
                        for item in products:
                            # if item.count_in_uom > 0:
                            name = item.name
                            if item.default_code:
                                name = '[' + item.default_code + ']' + name
                            price = product_unit_price * item.uom_id.factor_inv
                            uom = item.uom_id.name

                            prices_all = self.env['customer.product.price']
                            for rec in self.order_id.partner_id.customer_pricelist_ids:
                                if not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= date.today():
                                    prices_all |= rec.pricelist_id.customer_product_price_ids

                            prices_all = prices_all.filtered(lambda r: r.product_id.id == item.id)
                            product_price_rec = self.env['customer.product.price']
                            msg = ''
                            for price_rec in prices_all:
                                if price_rec.pricelist_id.type == 'customer' and not price_rec.partner_id and prices_all.filtered(
                                        lambda r: r.partner_id):
                                    continue

                                product_price_rec = price_rec
                                break
                            if product_price_rec:
                                price = price_rec.price
                                uom = price_rec.product_uom.name

                            similar_product_price += "<tr><td>{}</td><td>{:.02f}</td><td>{}</td></tr>".format(name,
                                                                                                              price,
                                                                                                              uom)
                        similar_product_price += "</table>"
                        self.similar_product_price = similar_product_price
                    else:
                        self.similar_product_price = False
        return res

    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_remaining_qty(self):
        for line in self:
            line.remaining_qty = line.product_uom_qty - line.qty_delivered

    @api.depends('product_id.volume', 'product_id.weight')
    def _compute_gross_weight_volume(self):
        for line in self:
            line.gross_volume = line.product_id.volume * line.product_qty
            line.gross_weight = line.product_id.weight * line.product_qty

    @api.depends('product_id', 'product_uom')
    def _compute_lst_cost_prices(self):
        for line in self:
            if line.product_id and line.product_uom:
                uom_price = line.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == line.product_uom)
                if uom_price:
                    line.lst_price = uom_price[0].price
                    if line.product_id.cost:
                        line.working_cost = uom_price[0].cost
                else:
                    line.product_id.job_queue_standard_price_update()
                    uom_price = line.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == line.product_uom)
                    if uom_price:
                        line.lst_price = uom_price[0].price
                        if line.product_id.cost:
                            line.working_cost = uom_price[0].cost
            if line.is_delivery and line.order_id.carrier_id and line.order_id.carrier_id.delivery_type not in [
                'base_on_rule', 'fixed']:
                line.working_cost = line.order_id.delivery_cost
                line.lst_price = line.order_id.delivery_price

    def unlink(self):
        """
         allow delete delivery line in a confirmed order
        """
        if self.exists():
            base = None
            unlinked_lines = self.env['sale.order.line']
            cascade_line = self.env['sale.order.line']
            for parentClass in self.__class__.__bases__:
                if parentClass._name == 'base':
                    base = parentClass
            lines_exist = 0
            delivery_lines = [delivery_line for delivery_line in self if delivery_line.is_delivery]
            if delivery_lines:
                lines_exist = len(delivery_lines)
            for line in self:

                if line.is_delivery and line.order_id.state == 'sale' and lines_exist == 1:
                    raise ValidationError(
                        'You cannot delete a Delivery line,since the sale order is already confirmed,please refresh the page to undo')
                if line.is_delivery and base:
                    base.unlink(line)
                    unlinked_lines |= line
                elif line.exists() and line.product_id.need_sub_product:
                    cascade_line |= line + line.order_id.order_line.filtered(lambda rec: rec.is_addon)
                elif line.exists():
                    master_product = line.order_id.order_line.mapped('product_id').filtered(
                        lambda rec: rec.need_sub_product and line.product_id in rec.product_addons_list)
                    addon_products = master_product.product_addons_list
                    if master_product:
                        raise UserError(_(
                            "Product {} must be sold with \n\n {} \n\ncan't be removed without removing {}. \n\n Please refresh the page...!").format(
                            master_product.name, '\n'.join(['➥ ' + product.name for product in addon_products]),
                            master_product.name))

            return super(SaleOrderLine, (self - unlinked_lines) + cascade_line).unlink()

    def name_get(self):
        result = []
        for line in self:
            result.append((line.id, "%s - %s - %s - %s" % (
                line.order_id.name, line.name, line.product_uom.name, line.order_id.date_order)))
        return result

    def update_price_list(self):
        """
        Update pricelist
        """
        if not self.is_delivery and not self.is_downpayment:
            unit_price = self.price_unit
            if self.product_id.uom_id == self.product_uom and self.product_uom_qty % 1 != 0.0:
                numer = self.price_unit * self.product_uom_qty
                denom = (int(self.product_uom_qty / 1.0) + (
                        (self.product_uom_qty % 1) * (100 + self.product_id.categ_id.repacking_upcharge) / 100))
                unit_price = numer / denom
            unit_price = float_round(unit_price, precision_digits=2)

            partner = self.order_id.partner_id.id
            if not self.order_id.storage_contract:

                partner_history = self.env['sale.order.line'].search(
                    [('product_id', '=', self.product_id.id), ('shipping_id', '=', self.shipping_id.id),
                     ('is_last', '=', True), ('product_uom', '=', self.product_uom.id)])
                partner_history and partner_history.write({'is_last': False})
                self.write({'is_last': True})

                sale_history = self.env['sale.history'].search(
                    [('partner_id', '=', partner), ('product_id', '=', self.product_id.id),
                     ('uom_id', '=', self.product_uom.id), '|', ('active', '=', True), ('active', '=', False)], limit=1)
                if sale_history:
                    sale_history.order_line_id = self
                else:
                    self.env['sale.history'].create({'order_line_id': self.id, 'partner_id': partner})

                sale_tax_history = self.env['sale.tax.history'].search(
                    [('partner_id', '=', self.order_id.partner_shipping_id.id),
                     ('product_id', '=', self.product_id.id)],
                    limit=1)
                is_tax = False
                if self.tax_id:
                    is_tax = True
                if sale_tax_history:
                    sale_tax_history.tax = is_tax
                else:
                    vals = {'product_id': self.product_id.id,
                            'partner_id': self.order_id.partner_shipping_id.id,
                            'tax': is_tax
                            }
                    self.env['sale.tax.history'].create(vals)

            # Create record in customer.product.price if not exist
            # if exist then check the price and update
            # if shared price exists then do not proceed with record creation

            if self.price_from and self.price_from.pricelist_id.type != 'competitor':
                if self.price_from.price != unit_price:
                    self.price_from.with_context({'from_sale': True}).price = unit_price
                    self.manual_price = True
            else:
                prices_all = self.env['customer.product.price']
                for rec in self.order_id.partner_id.customer_pricelist_ids:
                    if rec.pricelist_id.type in ('shared', 'customer') and (
                            not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= date.today()):
                        prices_all |= rec.pricelist_id.customer_product_price_ids
                prices_all = prices_all.filtered(
                    lambda r: r.product_id.id == self.product_id.id and r.product_uom.id == self.product_uom.id and (
                            not r.partner_id or r.partner_id.id == self.order_id.partner_shipping_id.id))
                price_from = False
                for price_rec in prices_all:

                    if not price_rec.partner_id and prices_all.filtered(lambda r: r.partner_id):
                        continue
                    price_from = price_rec
                    break
                if price_from:
                    if price_from.price < unit_price:
                        price_from.with_context({'from_sale': True}).price = unit_price
                        self.manual_price = True
                else:
                    price_lists = self.order_id.partner_id.customer_pricelist_ids.filtered(
                        lambda r: r.pricelist_id.type == 'customer').sorted(key=lambda r: r.sequence)

                    if not price_lists:
                        product_pricelist = self.env['product.pricelist'].create({
                            'name': self.order_id.partner_id.customer_code,
                            'type': 'customer',
                        })
                        price_lists = self.env['customer.pricelist'].create({
                            'pricelist_id': product_pricelist.id,
                            'partner_id': self.order_id.partner_id.id,
                            'sequence': 0
                        })
                    else:
                        price_from = price_lists[0].pricelist_id.customer_product_price_ids.filtered(
                            lambda r: r.product_id.id == self.product_id.id and r.product_uom.id == self.product_uom.id)
                        if price_from:
                            if price_from.price < unit_price:
                                price_from.with_context({'from_sale': True}).price = unit_price
                                self.manual_price = True
                    if not price_from:
                        price_from = self.env['customer.product.price'].with_context({'from_sale': True}).create({
                            'partner_id': self.order_id.partner_shipping_id.id,
                            'product_id': self.product_id.id,
                            'product_uom': self.product_uom.id,
                            'pricelist_id': price_lists[0].pricelist_id.id,
                            'price': unit_price
                        })
                    self.new_product = True
                if price_from:
                    self.price_from = price_from.id

    def write(self, vals):
        for line in self:
            if vals.get('price_unit') and line.order_id.state == 'sale':
                if not self.env.user.has_group('sales_team.group_sale_manager') and line.product_id.type != 'service':
                    if line.working_cost > line.price_unit > vals.get('price_unit'):
                        raise ValidationError(
                            _('You are not allowed to reduce price below product cost. Contact your sales Manager.'))
                    if line.price_unit >= line.working_cost > vals.get('price_unit'):
                        raise ValidationError(
                            _('You are not allowed to reduce price below product cost. Contact your sales Manager.'))
        res = super().write(vals)
        for line in self:
            if vals.get('price_unit') and line.order_id.state == 'sale':
                line.update_price_list()
        return res

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        values.update({
            'date_planned': self.order_id.release_date
        })
        return values

    def _action_launch_stock_rule_not_migrated(self, previous_product_uom_qty=False):

        """
        override to keep the UOM same as sales uom, now this feature added in base using a parama
        stock.propagate_uom
        added in data
        method not needed
        """
        pass

    @api.model
    def create(self, vals):
        line = super(SaleOrderLine, self).create(vals)
        if line.state == 'sale' and line.move_ids:
            msg = "Extra line with %s " % line.product_id.display_name
            line.move_ids.mapped('picking_id').filtered(lambda rec: rec.state != 'cancel').message_post(body=msg)
        if line.product_id.need_sub_product and line.product_id.product_addons_list:
            for product_addon in line.product_id.product_addons_list.filtered(
                    lambda rec: rec.id not in [line.order_id.order_line.mapped('product_id').ids]):
                addon_line = self.create({
                    'product_id': product_addon.id,
                    'product_uom': product_addon.uom_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'order_id': line.order_id.id,
                    'is_addon': True
                })
                addon_line.product_id_change()

        if line.order_id.state == 'sale':
            line.update_price_list()

        if line.note_type == 'permanant':
            note = self.env['product.notes'].search([
                ('product_id', '=', line.product_id.id),
                ('partner_id', '=', line.order_id.partner_id.id),
                ('expiry_date', '>', date.today())
            ], limit=1)
            if not note:
                self.env['product.notes'].create({
                    'product_id': line.product_id.id,
                    'partner_id': line.order_id.partner_id.id,
                    'notes': line.note,
                    'expiry_date': line.note_expiry_date
                })
            else:
                note.notes = line.note
                note.expiry_date = line.note_expiry_date
        return line

    @api.onchange('product_id', 'product_uom', 'order_partner_id')
    def onchange_get_last_sale_info(self):
        """
        get last sale detail of the product by the partner.
        """
        if self.product_id and self.product_uom:
            if not self.order_id.partner_id:
                raise ValidationError('Please enter customer information first.')

            last = self.env['sale.history'].sudo().search([
                ('partner_id', '=', self.order_id.partner_id.id),
                ('product_id', '=', self.product_id.id),
                ('uom_id', '=', self.product_uom.id)
            ], limit=1)
            if last:
                local = pytz.timezone(self.sudo().env.user.tz or "UTC")
                last_date = datetime.strftime(
                    pytz.utc.localize(
                        datetime.strptime(
                            str(last.order_id.date_order), DEFAULT_SERVER_DATETIME_FORMAT)
                    ).astimezone(local), "%m/%d/%Y %H:%M:%S")
                self.last_sale = 'Order Date  - %s\nPrice Unit    - %s\nSale Order  - %s' % (
                    last_date, last.order_line_id.price_unit, last.order_id.name)
            else:
                self.last_sale = 'No Previous information Found'
        else:
            self.last_sale = 'No Previous information Found'

    @api.onchange('product_id')
    def product_id_change(self):
        """
        Add taxes automatically to sales lines if partner has a
        resale number and no taxes charged based on previous
        purchase history.
        Display a message from which pricelist the unit price is taken .

        """

        res = super(SaleOrderLine, self).product_id_change()
        if not res:
            res = {}
        lst_price = 0
        vals = {}
        working_cost = 0
        if not self.product_id:
            vals.update({'lst_price': lst_price, 'working_cost': working_cost})
        else:
            warn_msg = not self.product_id.purchase_ok and "This item can no longer be purchased from vendors" or ""
            if not self.order_id.storage_contract and sum(
                    [1 for line in self.order_id.order_line if line.product_id.id == self.product_id.id]) > 1:
                warn_msg += "\n{} is already in SO.".format(self.product_id.name)

            if self.order_id:
                partner_history = self.env['sale.tax.history'].search(
                    [('partner_id', '=', self.order_id and self.order_id.partner_shipping_id.id or False),
                     ('product_id', '=', self.product_id and self.product_id.id)])
                if self.order_id.partner_id and not self.order_id.partner_id.vat:
                    partner_history = False
                if partner_history and not partner_history.tax:
                    self.tax_id = [(5, _, _)]

                # force domain the tax_id field with only available taxes based on applied fpos
                if res and not res.get('domain', False):
                    res.update({'domain': {}})
                pro_tax_ids = self.product_id.taxes_id
                if self.order_id.fiscal_position_id:
                    taxes_ids = self.order_id.fiscal_position_id.map_tax(pro_tax_ids).ids
                    res.get('domain', {}).update({'tax_id': [('id', 'in', taxes_ids)]})

            msg, product_price, price_from = self.calculate_customer_price()
            warn_msg += msg and "\n\n{}".format(msg)
            if self.product_id.sale_delay > 0:
                warn_msg += 'product: {} takes {} days to be procured.'.format(self.product_id.name,
                                                                               self.product_id.sale_delay)
            if warn_msg:
                res.update({'warning': {'title': 'Warning!', 'message': warn_msg}})

            vals.update({'price_unit': product_price, 'price_from': price_from})

            # for uom only show those applicable uoms
            domain = res.get('domain', {})
            product_uom_domain = domain.get('product_uom', [])
            product_uom_domain.append(('id', 'in', self.product_id.sale_uoms.ids))

            # get this customers last time sale description for this product and update it in the line
            note = self.env['product.notes'].search(
                [('product_id', '=', self.product_id.id),
                 ('partner_id', '=', self.order_id.partner_id.id),
                 ('expiry_date', '>', date.today())], limit=1)
            if note:
                self.note = note.notes
                self.note_expiry_date = note.expiry_date
            else:
                self.note = ''
        self.update(vals)

        return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        """
        assign the price unit from customer_product_price
        based on the pricelist.
        If there is no pricelist assign the standard price of product.
        """

        old_unit_price = self.price_unit
        res = super(SaleOrderLine, self).product_uom_change()
        res = res and res or {}
        warning, product_price, price_from = self.calculate_customer_price()
        if self.product_id and self.storage_contract_line_id:
            contract_line = self.storage_contract_line_id
            remaining_qty = contract_line.storage_remaining_qty
            if remaining_qty <= contract_line.selling_min_qty:
                self.product_uom_qty = remaining_qty
                self.price_unit = 0
            elif self.product_uom_qty <= remaining_qty:
                if self.product_uom_qty < contract_line.selling_min_qty:
                    warning_mess = {
                        'title': _('Less than Minimum qty'),
                        'message': _('You are going to sell less than minimum qty in the contract.')
                    }
                    self.product_uom_qty = 0
                    res.update({'warning': warning_mess})
                else:
                    self.price_unit = 0
            elif self.product_uom_qty > remaining_qty:
                warning_mess = {
                    'title': _('More than Storage contract'),
                    'message': _(
                        'You are going to Sell more than in storage contract.Only %s is remaining in this contract.' % (
                            remaining_qty))
                }
                self.product_uom_qty = 0
                res.update({'warning': warning_mess})
        else:
            if self._context.get('quantity', False):
                self.price_unit = old_unit_price
            else:
                self.price_unit = product_price
            self.price_from = price_from
            res = res and res or {}
            if self.product_uom_qty % 1 != 0.0:
                warning_mess = {
                    'title': _('Fractional Qty Alert!'),
                    'message': _('You plan to sell Fractional Qty.')
                }
                res.update({'warning': warning_mess})
        return res

    def calculate_customer_price(self):
        """
        Fetch unit price from the relevant pricelist of partner
        if product is not found in any pricelist,set
        product price as Standard price of product
        """
        prices_all = self.env['customer.product.price']
        for rec in self.order_id.partner_id.customer_pricelist_ids:
            if not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= date.today():
                prices_all |= rec.pricelist_id.customer_product_price_ids

        prices_all = prices_all.filtered(
            lambda r: r.product_id.id == self.product_id.id and r.product_uom.id == self.product_uom.id and (
                    not r.partner_id or r.partner_id.id == self.order_id.partner_shipping_id.id or r.partner_id.id == self.order_id.partner_id.id))
        product_price = 0.0
        price_from = False
        msg = ''
        for price_rec in prices_all:

            if price_rec.pricelist_id.type == 'customer' and not price_rec.partner_id and prices_all.filtered(
                    lambda r: r.partner_id):
                continue

            if price_rec.pricelist_id.type not in ('customer', 'shared'):
                msg = "Unit price of this product is fetched from the pricelist %s." % (price_rec.pricelist_id.name)
            product_price = price_rec.price
            price_from = price_rec.id
            break
        if not price_from:
            if self.product_id and self.product_uom:
                uom_price = self.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == self.product_uom)
                if uom_price:
                    product_price = uom_price[0].price

            msg = "Unit Price for this product is not found in any pricelists, fetching the unit price as product standard price."

        if self.product_id.uom_id == self.product_uom and self.product_uom_qty % 1 != 0.0:
            product_price = ((int(self.product_uom_qty / 1) * product_price) + (
                    (self.product_uom_qty % 1) * product_price * (
                    (100 + self.product_id.categ_id.repacking_upcharge) / 100))) / self.product_uom_qty
        product_price = float_round(product_price, precision_digits=2)
        return msg, product_price, price_from

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
