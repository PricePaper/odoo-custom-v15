# -*- coding: utf-8 -*-

import calendar
import logging as server_log
from math import ceil

import datetime
from dateutil.relativedelta import *

from odoo import fields, models, api
from odoo.addons.queue_job.job import job

to_date_hardcoded = datetime.datetime.strptime('2017-12-28', '%Y-%m-%d').date()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_op_update_date = fields.Datetime(string='Last Orderpoint Update Date')
    forecast_days = fields.Integer(string="Forecast Days", default=30)
    orderpoint_update_date = fields.Date(string='Orderpoint Update Date')
    dont_use_fbprophet = fields.Boolean(string='Do not use Fbprophet Forecasting')
    past_days = fields.Integer(string="Fbprophet Hist Days",
                               help="Days worth of historical data to be taken into consideration for Fbprophet calculation",
                               default=1825)

    @api.multi
    def get_fbprophet_config(self):
        """
        Return specific fbprophet configuration
        """

        config = self.env['fbprophet.config'].search([('config_type', '=', 'inventory')]) or False
        if config:
            product_config = config.filtered(lambda r: r.inv_config_for == 'product' and r.product_id == self)
            if product_config:
                return product_config[0]
            categ_config = config.filtered(lambda r: r.inv_config_for == 'categ' and r.categ_id == self.categ_id)
            if categ_config:
                return categ_config[0]
            global_config = config.filtered(lambda r: r.inv_config_for == 'global')
            if global_config:
                return global_config[0]

        config = self.env['fbprophet.config'].search([('config_type', '=', 'default')], limit=1) or False
        return config

    @api.multi
    def forecast_sales(self, periods=30, freq='d', to_date=str(datetime.date.today())):
        """
        Forecast the sale of a product in daily basis by collecting
        past 5 years sales details
        """

        to_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
        if periods == 30 and freq == 'd':
            forecast_from = (to_date + relativedelta(days=1))

            month_last_date = calendar.monthrange(forecast_from.year, forecast_from.month)[1]
            periods = month_last_date

        self.ensure_one()
        config = self.get_fbprophet_config()
        from_date = (to_date - relativedelta(days=self.past_days)).strftime('%Y-%m-%d')
        product_ids = [self.id]
        forecast = []
        if self.superseded:
            product_ids += self.superseded.mapped('old_product').ids
        query = """
                SELECT to_char(o.date_order, 'YYYY-MM-DD')as
                year_month_day, sum(l.product_uom_qty), l.product_uom from sale_order o, sale_order_line
                l WHERE o.date_order >= '%s'
                AND o.date_order <= '%s' AND o.id=l.order_id AND
                l.product_id in (%s) AND l.product_uom_qty>0 AND o.state IN ('sale', 'done') GROUP BY l.product_uom, year_month_day ORDER BY year_month_day;""" % (
        from_date, str(to_date), (",".join(str(x) for x in product_ids)))

        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        if result:
            result = self.filler_to_append_zero_qty(result, to_date)
            date_to = (to_date + relativedelta(days=periods)).strftime('%Y-%m-%d')
            try:
                forecast = self.env['odoo_fbprophet.prophet.bridge'].run_prophet(result, from_date, date_to,
                                                                                 periods=periods, freq=freq,
                                                                                 config=config)
            except Exception as e:
                server_log.error("Exception in run_prophet for product %s" % (self.name))
                server_log.error(e)
        else:
            server_log.error("No data available for the product %s to forecast sales" % (self.name))
        return forecast

    @api.model
    def get_qty_from_orders(self, product_id, forecast_begin):
        to_date = datetime.datetime.strptime(forecast_begin, "%Y-%m-%d").date()
        forecast_end = (to_date + relativedelta(months=1)).strftime('%Y-%m-%d')
        orders = self.env['sale.order'].search(
            [('confirmation_date', '>', forecast_begin), ('confirmation_date', '<', str(forecast_end))])
        qty = 0.00
        for order in orders:
            for line in order.order_line:
                if line.product_id and line.product_id.id == product_id:
                    if line.product_uom == line.product_id.uom_id:
                        qty += line.product_uom_qty
                    else:
                        sale_uom_factor = line.product_uom.factor
                        qty += ((line.product_uom_qty * self.uom_id.factor) / sale_uom_factor)
        return qty

    @api.multi
    def show_forecast(self):
        """
        Return a graph and pivot views which are
        ploted with the forecast result
        """
        to_date = datetime.date.today()
        self.ensure_one()
        periods = self.forecast_days or 31
        forecast = self.forecast_sales(periods=periods, freq='d', to_date=str(to_date))
        self.env['product.forecast'].search([]).unlink()
        flag = False
        count = 0
        for ele in forecast:
            if datetime.datetime.strptime(ele[0], '%Y-%m-%d').date() >= to_date:
                flag = True
            if flag:
                count += 1
                self.env['product.forecast'].create({'product_id': self.id,
                                                     'date': ele[0],
                                                     'quantity': ele[1],  # quantity,
                                                     'quantity_min': ele[2],  # min_quantity,
                                                     'quantity_max': ele[3],  # max_quantity,
                                                     })

        #        if count>45:
        #            raise ValidationError(_("Graphical representation is not possible due to large data,Please minimize forecast days"))

        graph_id = self.env.ref('stock_orderpoint_enhancements.view_order_product_forecast_graph').id
        pivot_id = self.env.ref('stock_orderpoint_enhancements.view_order_product_forecast_pivot').id
        res = {
            "type": "ir.actions.act_window",
            "name": "Sale Forecast",
            "res_model": "product.forecast",
            "views": [[graph_id, "graph"], [pivot_id, "pivot"]],
            "domain": [["product_id", "=", self.id]],
            "target": "current",
        }

        return res

    @api.model
    def filler_to_append_zero_qty(self, result, to_date):
        """
        Process result of query by adding missing days
        with qty(0.0) between start_date and to_date
        Converts uom_qty into base uom_qty
        """
        res = []
        start_date = result and result[0] and result[0][0]
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()

        def _get_next_business_day(date):

            exclude_days = (4, 5)

            # Before 2019-04-26 trucks where loaded M-F, after 04-26 they were
            # loaded Su-Th
            if date < datetime.date(2019, 4, 26):
                exclude_days = (5, 6)

            next_date = date

            while True:
                next_date = next_date + relativedelta(days=1)
                if next_date.weekday() not in exclude_days:
                    return next_date
                continue

        while (start_date <= to_date):
            val = start_date.strftime("%Y-%m-%d")
            in_list = [rec for rec in result if rec and str(rec[0]) == val]

            if not in_list:
                res.append((val, 0.0))
            else:
                qty = 0
                for product_uom_qty in in_list:
                    if product_uom_qty[2] == self.uom_id.id:
                        qty += product_uom_qty[1]
                    else:
                        sale_uom_factor = self.env['uom.uom'].browse(product_uom_qty[2]).factor
                        qty += ((product_uom_qty[1] * self.uom_id.factor) / sale_uom_factor)
                res.append((val, qty))
            start_date = _get_next_business_day(start_date)
        return res

    @api.multi
    def calculate_qty(self, forecast, to_date, to_date_plus_delay):
        flag = False
        quantity = 0
        for ele in forecast:
            if datetime.datetime.strptime(ele[0], '%Y-%m-%d').date() >= to_date:
                flag = True
            if flag and ele[0] <= str(
                    to_date_plus_delay):  # calculate min and max qty between to_date and to_date_plus_delay
                quantity += ele[1]

        if quantity and self.env.user.company_id.buffer_percentages:
            quantity = ceil(quantity)
            # Buffer values stored as a Text field with the format of one expression:percent per line
            # e.g.
            # "<=5:0.50" meaning if the qty is less than or equal to 5, apply a 50% buffer
            # ">20:0.10" meaning if the qty is greater than 20 apply a 10% buffer
            lines = self.env.user.company_id.buffer_percentages.split()
            values_as_str = [x.split(':') for x in lines]
            values = [(x[0], float(x[1])) for x in values_as_str]

            for value in values:
                if eval(str(quantity) + value[0]):
                    quantity = quantity * (1.0 + value[1])
        return quantity

    @api.multi
    @job
    def job_queue_forecast(self):
        """
        cron method to set the orderpoints(OP) for every products
        uses fbprophet based forecasting for the OP setup.
        """

        to_date = datetime.date.today()

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

            min_forecast = self.forecast_sales(periods=delivery_lead_time, freq='d', to_date=str(to_date))
            min_quantity = self.calculate_qty(min_forecast, to_date, to_date_plus_delay)

            max_quantity = min_quantity
            if delivery_lead_time != max_delivery_lead_time:
                max_forecast = self.forecast_sales(periods=max_delivery_lead_time, freq='d', to_date=str(to_date))
                max_quantity = self.calculate_qty(max_forecast, to_date, max_to_date_plus_delay)

            orderpoint = self.orderpoint_ids and self.orderpoint_ids[0] or False

            if orderpoint:
                if not self.orderpoint_update_date or self.orderpoint_update_date < str(datetime.date.today()):
                    orderpoint.write({'product_min_qty': ceil(min_quantity),
                                      'product_max_qty': ceil(max_quantity),
                                      })
            else:
                self.env['stock.warehouse.orderpoint'].create({
                    'product_id': self.id,
                    'product_min_qty': ceil(min_quantity),
                    'product_max_qty': ceil(max_quantity),
                    'qty_multiple': 1,
                    'product_uom': self.uom_id.id,
                })
            self.last_op_update_date = str(datetime.datetime.today())
        return True

    @api.multi
    def reset_orderpoint(self):
        """
        Method to set the orderpoints(OP) for single product
        uses fbprophet based forecasting for the OP setup.
        """

        for product in self:
            product.with_delay(channel='root.Product_Orderpoint').job_queue_forecast()

    @api.model
    def set_orderpoint_cron(self):
        """
        cron method to set the orderpoints(OP) for every products
        uses fbprophet based forecasting for the OP setup.
        """

        products = self.env['product.product'].search(
            [('active', '=', True), ('type', '=', 'product'), ('dont_use_fbprophet', '=', False)],
            order='last_op_update_date')
        for product in products:
            product.with_delay(channel='root.Product_Orderpoint').job_queue_forecast()


ProductProduct()


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    delay = fields.Integer(
       string='Delivery Lead Time', required=True, default=0,
       help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")

    @api.multi
    def create(self, values):
        """
        Overriding create method to set delay

        """
        res = super(SupplierInfo, self).create(values)
        if res.delay == 0:
            res.delay = self.name.delay
        return res

    @api.multi
    def write(self, values):
        """
        Overriding write method to track changes in delivery lead time and
        reset orderpoint min/max qty according to delivery lead time
        """
        if 'delay' in values and values.get('delay', 0) == 0:
            values['delay'] = self.name.delay
        res = super(SupplierInfo, self).write(values)
        if 'delay' in values:
            product = self.product_id or self.env['product.product'].browse(
                self.product_tmpl_id.product_variant_id[0].id)
            self.reset_orderpoint(product)
        return res


    @api.onchange('name')
    def onchange_vendor(self):
        if self.name:
            self.delay = self.name.delay

    @api.multi
    def reset_orderpoint(self, product):
        """
        Reset min_qty and max_quantity in orderpoints
        based on the updated delivery lead time
        """
        self.ensure_one()
        forecast = product.job_queue_forecast()


SupplierInfo()
