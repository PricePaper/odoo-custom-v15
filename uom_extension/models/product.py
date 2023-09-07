# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round
from math import ceil
import datetime
import logging as server_log
from dateutil.relativedelta import *


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ppt_uom_id = fields.Many2one('uom.uom', string="PPT Uom id")

    reordering_min_qty_mod = fields.Float(
        compute='_compute_min_max_reordering_rules', compute_sudo=False)
    reordering_max_qty_mod = fields.Float(
        compute='_compute_min_max_reordering_rules', compute_sudo=False)

    @api.depends('reordering_min_qty', 'reordering_max_qty')
    def _compute_min_max_reordering_rules(self):
        for product in self:
            if product.ppt_uom_id:
                product.reordering_min_qty_mod = product.uom_id._compute_quantity(product.reordering_min_qty,
                                                                                  product.ppt_uom_id,
                                                                                  rounding_method='HALF-UP')
                product.reordering_max_qty_mod = product.uom_id._compute_quantity(product.reordering_max_qty,
                                                                                  product.ppt_uom_id,
                                                                                  rounding_method='HALF-UP')
            else:
                product.reordering_min_qty_mod = product.reordering_min_qty
                product.reordering_max_qty_mod = product.reordering_max_qty


class ProductProduct(models.Model):
    _inherit = 'product.product'

    uom_name = fields.Char(string='Unit of Measure Name', related='ppt_uom_id.name', readonly=True)
    quantity_available = fields.Float(
        'Quantity On Hand', compute='_compute_quantities_modified',
        digits='Product Unit of Measure',
        help="Current quantity of products.\n"
             "In a context with a single Stock Location, this includes "
             "goods stored at this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "stored in the Stock Location of the Warehouse of this Shop, "
             "or any of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.")
    incoming_quantity = fields.Float(
        'Incoming', compute='_compute_quantities_modified',
        digits='Product Unit of Measure',
        help="Quantity of planned incoming products.\n"
             "In a context with a single Stock Location, this includes "
             "goods arriving to this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods arriving to the Stock Location of this Warehouse, or "
             "any of its children.\n"
             "Otherwise, this includes goods arriving to any Stock "
             "Location with 'internal' type.")
    outgoing_quantity = fields.Float(
        'Outgoing', compute='_compute_quantities_modified',
        digits='Product Unit of Measure',
        help="Quantity of planned outgoing products.\n"
             "In a context with a single Stock Location, this includes "
             "goods leaving this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods leaving the Stock Location of this Warehouse, or "
             "any of its children.\n"
             "Otherwise, this includes goods leaving any Stock "
             "Location with 'internal' type.")

    virtually_available = fields.Float(
        'Forecasted Quantity', compute='_compute_quantities_modified',
        digits='Product Unit of Measure',
        help="Forecast quantity (computed as Quantity On Hand "
             "- Outgoing + Incoming)\n"
             "In a context with a single Stock Location, this includes "
             "goods stored in this location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.")
    qty_available_not_res_mod = fields.Float(
        string="Qty Available Not Reserved",
        digits="Product Unit of Measure",
        compute="_compute_qty_available_not_reserved_mod",
        help="Quantity of this product that is "
             "not currently reserved for a stock move",
    )
    sales_total_count = fields.Float(compute='_compute_sales_total_count', string='Sold')
    purchased_product_qty_mod = fields.Float(compute='_compute_purchased_product_qty_mod', string='Purchased')

    @api.onchange('sale_uoms')
    def onchange_sale_uoms(self):
        """
        """
        return {'domain': {
            'ppt_uom_id': ([('id', 'in', self.sale_uoms.ids)]),
            'uom_po_id': ([('id', 'in', self.sale_uoms.ids)]),
        }}

    def write(self, vals):
        ctx = dict(self._context)
        if 'uom_id' in vals:
            ctx.update({'check_uom_change': True})
        return super(ProductProduct, self.with_context(ctx)).write(vals)

    @api.depends('sales_count')
    def _compute_sales_total_count(self):
        for product in self:
            if product.ppt_uom_id:
                product.sales_total_count = float_round(product.sales_count,
                                                        precision_rounding=product.ppt_uom_id.rounding)

            else:
                product.sales_total_count = product.sales_count

    @api.depends('qty_available', 'incoming_qty', 'virtual_available', 'outgoing_qty')
    def _compute_quantities_modified(self):
        for product in self:
            print(product.uom_id, product.ppt_uom_id)
            if product.ppt_uom_id:
                product.quantity_available = product.uom_id._compute_quantity(product.qty_available, product.ppt_uom_id,
                                                                              rounding_method='HALF-UP')
                product.incoming_quantity = product.uom_id._compute_quantity(product.incoming_qty, product.ppt_uom_id,
                                                                             rounding_method='HALF-UP')

                product.outgoing_quantity = product.uom_id._compute_quantity(product.outgoing_qty, product.ppt_uom_id,
                                                                             rounding_method='HALF-UP')
                product.virtually_available = product.uom_id._compute_quantity(product.virtual_available,
                                                                               product.ppt_uom_id,
                                                                               rounding_method='HALF-UP')

            else:
                product.quantity_available = product.qty_available
                product.incoming_quantity = product.incoming_qty
                product.outgoing_quantity = product.outgoing_qty
                product.virtually_available = product.virtual_available

    def _compute_qty_available_not_reserved_mod(self):
        """
        override 3rd party module- stock_available_unreserved
        :return:
        """
        for product in self:
            if product.ppt_uom_id:
                product.qty_available_not_res_mod = product.uom_id._compute_quantity(product.qty_available_not_res,
                                                                                     product.ppt_uom_id,
                                                                                     rounding_method='HALF-UP')
            else:
                product.qty_available_not_res_mod = product.qty_available_not_res

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.quantity_done')
    def _compute_in_out_quantities(self):
        for product in self:
            # purchase_moves = product.stock_move_ids.filtered(lambda move: move.purchase_line_id and \
            #                                                               move.state not in ['cancel', 'done'])
            purchase_moves = self.env['stock.move'].search([('product_id', '=', product.id),
                                                            ('picking_code', '=', 'incoming'),
                                                            ('state', 'not in', ('cancel', 'done')),
                                                            ('picking_id.is_return', '=', False),
                                                            ('picking_id.rma_id', '=', False)])
            sale_moves = self.env['stock.move'].search([('product_id', '=', product.id),
                                                        ('picking_code', '=', 'outgoing'),
                                                        ('state', 'not in', ('cancel', 'done')),
                                                        ('picking_id.is_return', '=', False),
                                                        ('picking_id.state', 'not in',
                                                         ('in_transit', 'cancel', 'done', 'transit_confirmed')),
                                                        ('picking_id.rma_id', '=', False)])
            product_qty = 0
            for move in purchase_moves:
                product_qty += move.product_qty
            # converting to ppt_uom_id
            if product.ppt_uom_id:
                product.in_qty = product.uom_id._compute_quantity(product_qty, product.ppt_uom_id,
                                                                  rounding_method='HALF-UP')
            else:
                product.in_qty = product_qty

            product_qty = 0
            for move in sale_moves:
                product_qty += move.product_qty

            # converting to ppt_uom_id
            if product.ppt_uom_id:
                product.out_qty = product.uom_id._compute_quantity(product_qty, product.ppt_uom_id,
                                                                   rounding_method='HALF-UP')
            else:
                product.out_qty = product_qty

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.quantity_done')
    def _compute_transit_quantities(self):
        """
        overridden from batch delivery
        @return:
        """
        transit_location = self.env['stock.location'].search([('is_transit_location', '=', True)])
        qty_dict = self.with_context(location=transit_location.ids)._compute_quantities_dict(
            self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'),
            self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            # converting to ppt_uom_id
            if product.ppt_uom_id:
                product.transit_qty = product.uom_id._compute_quantity(qty_dict[product.id]['qty_available'],
                                                                       product.ppt_uom_id, rounding_method='HALF-UP')
            else:
                product.transit_qty = qty_dict[product.id]['qty_available']

    def _compute_lst_price_std_price(self):
        """overridden from price_paper module
           calculates standard price in new uom_id(ppt_uom_id)
        :return: None
        """
        for product in self:
            price = product.uom_standard_prices.filtered(lambda r: r.uom_id == product.ppt_uom_id)
            product.lst_from_std_price = price and price[0].price or 0

    @api.depends('purchased_product_qty')
    def _compute_purchased_product_qty_mod(self):
        for product in self:
            if product.ppt_uom_id:
                product.purchased_product_qty_mod = product.uom_id._compute_quantity(product.purchased_product_qty,
                                                                                     product.ppt_uom_id,
                                                                                     rounding_method='HALF-UP')
            else:
                product.purchased_product_qty_mod = product.purchased_product_qty

    def job_queue_forecast(self):
        """
        cron method to set the orderpoints(OP) for every products
        uses fbprophet based forecasting for the OP setup.
        """

        to_date = datetime.date.today()
        msg = ''

        vendor = self.seller_ids.filtered(lambda seller: seller.is_available) and \
                 self.seller_ids.filtered(lambda seller: seller.is_available)[0]
        if not vendor:
            server_log.error('Supplier is not set for product %s' % self.name)
        else:
            delivery_lead_time = vendor.delay or 0
            if not delivery_lead_time:
                delivery_lead_time = vendor.name.delay or 0
                if not delivery_lead_time:
                    server_log.error('Delivery lead time is not available for product %s' % self.name)

            max_delivery_lead_time = delivery_lead_time + (vendor.name.order_freq or 0)
            to_date_plus_delay = to_date + relativedelta(days=delivery_lead_time)
            max_to_date_plus_delay = to_date + relativedelta(days=max_delivery_lead_time)
            from_date = (to_date - relativedelta(days=self.past_days))
            config = self.get_fbprophet_config()
            if config.inv_config_for == 'categ':
                if config.end_date:
                    to_date = config.end_date
                if config.start_date:
                    from_date = config.start_date

            min_forecast = self.forecast_sales(config, str(from_date), periods=delivery_lead_time, freq='d',
                                               to_date=str(to_date))
            min_quantity = self.calculate_qty(min_forecast, to_date, to_date_plus_delay)

            max_quantity = min_quantity
            if delivery_lead_time != max_delivery_lead_time:
                max_forecast = self.forecast_sales(config, str(from_date), periods=max_delivery_lead_time, freq='d',
                                                   to_date=str(to_date))
                max_quantity = self.calculate_qty(max_forecast, to_date, max_to_date_plus_delay)

            orderpoint = self.env['stock.warehouse.orderpoint'].search(
                ['|', ('active', '=', False), ('active', '=', True), ('product_id', '=', self.id)])
            orderpoint = orderpoint and orderpoint[0] or False

            # converting to new uom
            if orderpoint:
                if not self.orderpoint_update_date or self.orderpoint_update_date < str(datetime.date.today()):
                    orderpoint.write({'product_min_qty_mod': ceil(min_quantity) if self.ppt_uom_id else 0,
                                        'product_max_qty_mod': ceil(max_quantity) if self.ppt_uom_id else 0,
                                        'active': True
                                          })
            else:
                values = {
                    'product_id': self.id,
                    'product_min_qty_mod': ceil(min_quantity),
                    'product_max_qty_mod': ceil(max_quantity),
                    'qty_multiple': 1,
                    'product_uom': self.uom_id.id,
                    'product_ppt_uom': self.ppt_uom_id.id if self.ppt_uom_id else False,
                }
                self.env['stock.warehouse.orderpoint'].create(values)
            self.last_op_update_date = datetime.datetime.today()
            msg = 'Min qty: ' + str(ceil(min_quantity)) + '\n' + 'Max qty: ' + str(ceil(max_quantity))
        return msg

    @api.model
    def filler_to_append_zero_qty(self, result, to_date, from_date):
        """
        Process result of query by adding missing days
        with qty(0.0) between start_date and to_date
        Converts uom_qty into base uom_qty
        """
        res = []
        start_date = result and result[0] and result[0][0]
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        # converting to ppt_uom_id
        while (start_date <= to_date):
            val = start_date.strftime("%Y-%m-%d")
            in_list = [rec for rec in result if rec and str(rec[0]) == val]

            if not in_list:
                res.append((val, 0.0))
            else:
                qty = 0
                # modified to handle uom change
                uom_id = self.ppt_uom_id if self.ppt_uom_id else self.uom_id
                for product_uom_qty in in_list:
                    if product_uom_qty[2] == uom_id.id:
                        qty += product_uom_qty[1]
                    else:
                        sale_uom_factor = self.env['uom.uom'].browse(product_uom_qty[2]).factor
                        qty += ((product_uom_qty[1] * uom_id.factor) / sale_uom_factor)
                res.append((val, qty))
            start_date = start_date + relativedelta(days=1)
        return res

    def _compute_quantities(self):
        """
        overridden from batch delivery custom module,
        either remove the function or overwrite there to avoid repetition
        @return:
        """
        super(ProductProduct, self)._compute_quantities()
        for product in self:
            product.outgoing_quantity -= product.transit_qty
