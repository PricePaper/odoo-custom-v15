# -*- coding: utf-8 -*-

import calendar
import datetime
import logging as server_log
from math import ceil
from odoo.exceptions import UserError

from dateutil.relativedelta import *

from odoo import fields, models, api, _
#from odoo.addons.queue_job.job import job TODO uncomment me

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

    def reset_orderpoint(self):
        """
        Method to set the orderpoints(OP) for single product
        uses fbprophet based forecasting for the OP setup.
        """

        for product in self:
            product.job_queue_forecast()


    def get_number_of_days(self):
        """
        Get number of days through a wizard
        """
        view_id = self.env.ref('stock_orderpoint_enhancements.view_prophet_days_wiz').id
        return {
            'name': _('FBProphet Forecast Days'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'prophet.forecast.days',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


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

    # @api.multi
    # def reset_orderpoint(self, product):
    #     """
    #     Reset min_qty and max_quantity in orderpoints
    #     based on the updated delivery lead time
    #     """
    #     self.ensure_one()
    #     forecast = product.job_queue_forecast()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
