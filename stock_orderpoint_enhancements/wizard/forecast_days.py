# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
from odoo.exceptions import UserError

class CostChangePercentage(models.TransientModel):
    _name = 'prophet.forecast.days'
    _description = "FB prophet forecast days"

    number_of_days = fields.Integer(string='# of days', default=30)
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')

    @api.onchange('from_date')
    def onchange_from_date(self):
        if self.from_date and self.from_date < datetime.date.today():
            return {'warning': {'title': 'Warning', 'message': 'From Date is less than today'}}


    def show_forecast(self):
        """
        Show forecast
        """
        if self.from_date > self.to_date:
            raise UserError(_("From date should be less than To date."))

        active_id = self._context.get('active_id')
        product = self.env['product.product'].browse(active_id)
        forecast, to_date = product.show_forecast(self.from_date, self.to_date)


        self.env['product.forecast'].search([]).unlink()
        flag = False
        count = 0
        for ele in forecast:
            if datetime.datetime.strptime(ele[0], '%Y-%m-%d').date() >= self.from_date:
                flag = True
            if flag:
                count += 1

                self.env['product.forecast'].create({
                    'product_id': product.id,
                    'date': ele[0],
                    'quantity': ele[1],  # quantity,
                    'quantity_min': ele[2],  # min_quantity,
                    'quantity_max': ele[3],  # max_quantity,
                })

        graph_id = self.env.ref('stock_orderpoint_enhancements.view_order_product_forecast_graph').id
        pivot_id = self.env.ref('stock_orderpoint_enhancements.view_order_product_forecast_pivot').id
        res = {
            "type": "ir.actions.act_window",
            "name": "Sale Forecast",
            "res_model": "product.forecast",
            "views": [[graph_id, "graph"], [pivot_id, "pivot"]],
            "domain": [["product_id", "=", product.id]],
            "target": "current",
        }
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
