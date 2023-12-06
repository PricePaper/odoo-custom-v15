# -*- coding: utf-8 -*-

import calendar
import datetime
import logging as server_log
from math import ceil
from odoo.exceptions import UserError

from dateutil.relativedelta import *

from odoo import fields, models, api, _


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


    def action_view_stock_move_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_line_action")
        action['domain'] = [('product_id', '=', self.id),('location_dest_id.is_transit_location','=',False)]
        return action


    def reset_orderpoint(self):
        """
        Method to set the orderpoints(OP) for single product
        uses fbprophet based forecasting for the OP setup.
        """

        for product in self:
            product.job_queue_forecast()


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


    def get_number_of_days(self):
        """
        Get number of days through a wizard
        """
        view_id = self.env.ref('stock_orderpoint_enhancements.view_prophet_days_wiz').id
        return {
            'name': _('FBProphet Forecast Days'),
            'view_mode': 'form',
            'res_model': 'prophet.forecast.days',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def forecast_sales(self, config, from_date, periods=30, freq='d', to_date=str(datetime.date.today())):
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
        config = config
        from_date = from_date
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

        result = []
        # result is too large for fetchall()
        while True:
            rows = self.env.cr.fetchmany()

            if rows:
                result.extend(rows)
            else:
                break
        if result:
            result = self.filler_to_append_zero_qty(result, to_date, from_date)
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

#    def get_qty_from_orders(self, product_id, forecast_begin): Note this function is not migrated as it is wriiten for script purpose,not ussing now


    def job_queue_forecast(self):
        """
        cron method to set the orderpoints(OP) for every products
        uses fbprophet based forecasting for the OP setup.
        """

        to_date = datetime.date.today()
        msg=''

        vendor = self.seller_ids.filtered(lambda s: (s.date_start and s.date_end and s.date_start < to_date and s.date_end > to_date) or (not s.date_start or not s.date_end))

        if not vendor:
            server_log.error('Supplier is not set for product %s' % self.name)
        else:
            vendor = vendor[0]
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

            min_forecast = self.forecast_sales(config, str(from_date), periods=delivery_lead_time, freq='d', to_date=str(to_date))
            min_quantity = self.calculate_qty(min_forecast, to_date, to_date_plus_delay)

            max_quantity = min_quantity
            if delivery_lead_time != max_delivery_lead_time:
                max_forecast = self.forecast_sales(config, str(from_date), periods=max_delivery_lead_time, freq='d', to_date=str(to_date))
                max_quantity = self.calculate_qty(max_forecast, to_date, max_to_date_plus_delay)

            orderpoint = self.env['stock.warehouse.orderpoint'].search(['|', ('active', '=', False), ('active', '=',True), ('product_id', '=', self.id)])
            orderpoint = orderpoint and orderpoint[0] or False
            if orderpoint:
                if not self.orderpoint_update_date or self.orderpoint_update_date < str(datetime.date.today()):
                    orderpoint.write({'product_min_qty': ceil(min_quantity),
                                      'product_max_qty': ceil(max_quantity),
                                      'active': True
                                      })
            else:
                self.env['stock.warehouse.orderpoint'].create({
                    'product_id': self.id,
                    'product_min_qty': ceil(min_quantity),
                    'product_max_qty': ceil(max_quantity),
                    'qty_multiple': 1,
                    'product_uom': self.uom_id.id,
                })
            self.last_op_update_date = datetime.datetime.today()
            msg = 'Min qty: ' + str(ceil(min_quantity)) + '\n' + 'Max qty: ' +  str(ceil(max_quantity))
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
            start_date = start_date + relativedelta(days=1)
        return res

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
                    break
        return quantity

    @api.model
    def set_orderpoint_cron(self):
        """
        cron method to set the orderpoints(OP) for every products
        uses fbprophet based forecasting for the OP setup.
        """
        name1 = 'Order Point: '
        products = self.env['product.product'].search(
            [('active', '=', True), ('type', '=', 'product'), ('dont_use_fbprophet', '=', False), ('purchase_ok', '=', True)],
            order='last_op_update_date')
        for product in products:
            name = product.default_code and product.default_code or product.name
            name = name1+name
            product.with_delay(description=name, channel='root.Product_Orderpoint').job_queue_forecast()

    def action_reset_order_point(self):
        """
        Action menu from product view to reset orderpoint
        """
        name1 = 'Order Point: '
        for product in self:
            name = product.default_code and product.default_code or product.name
            name = name1+name
            product.with_delay(description=name, channel='root.Product_Orderpoint').job_queue_forecast()

    def show_forecast(self, forecast_fr_date, forecast_to_date):
        """
        Return a graph and pivot views which are
        ploted with the forecast result
        """
        to_date = forecast_fr_date
        self.ensure_one()
        from_date = (to_date - relativedelta(days=self.past_days)).strftime('%Y-%m-%d')
        periods = (forecast_to_date - to_date).days
        config = self.get_fbprophet_config()
        if not config:
            raise UserError(_("FB prophet configuration not found"))
        if config.inv_config_for == 'categ':
            if config.end_date:
                to_date = config.end_date
            if config.start_date:
                from_date = config.start_date

        forecast = self.forecast_sales(config, str(from_date), periods=periods, freq='d', to_date=str(to_date))
        return forecast, to_date

class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    delay = fields.Integer(
        string='Delivery Lead Time', required=True, compute='_compute_delay', store=False,
        help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.A value of zero (0) will tell the system to use the delay provided by the product vendor")
    manual_delay = fields.Integer(string='Delivery Lead Time', default=0)

    def _compute_delay(self):
        for rec in self:
            if rec.manual_delay == 0:
                rec.delay = rec.name.delay
            else:
                rec.delay = rec.manual_delay


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
