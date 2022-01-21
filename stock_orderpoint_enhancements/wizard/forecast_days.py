# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime

class CostChangePercentage(models.TransientModel):
    _name = 'prophet.forecast.days'
    _description = "FB prophet forecast days"

    number_of_days = fields.Integer(string='# of days', default=30)


    def show_forecast(self):
        """
        Show forecast
        """

        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
