# -*- coding: utf-8 -*-

import calendar
import logging as server_log
from datetime import datetime

from dateutil.easter import easter

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

try:
    import pandas as pd
    #    import numpy as np
    from fbprophet import Prophet
    from pandas.tseries.holiday import USFederalHolidayCalendar
    import holidays as pypiholidays
except ImportError as e:
    server_log.error(e)

class YearlyHolidays(models.Model):
    _name = 'yearly.holidays'
    _description = 'Yearly Holidays'
    _order = 'name'

    name = fields.Char(string='Year', required=True)
    days = fields.One2many('holiday.day', 'year_id', string='Days')


    def get_holidays(self):
        """
        Get all US federal holidays
        in the given year
        """
        self.ensure_one()
        cal = USFederalHolidayCalendar()
        start = "%s-01-01" % (self.name)
        end = "%s-12-31" % (self.name)
        holidays = cal.holidays(start=start, end=end).to_pydatetime()
        holidays = [t.strftime('%Y-%m-%d') for t in holidays]
        # Add in Easter
        holidays.append(easter(int(self.name)))

        existing_holidays = self.env['holiday.day'].search([('year_id', '=', self.id)])
        existing_holidays = [h.date for h in existing_holidays]
        us_holidays = pypiholidays.UnitedStates()

        for holiday in holidays:
            holiday_name = us_holidays.get(holiday)
            if holiday in existing_holidays:
                continue
            self.env['holiday.day'].create({'description': holiday_name, 'date': holiday, 'year_id': self.id})


class Holiday(models.Model):
    _name = 'holiday.day'
    _description = 'Holiday'
    _order = 'date'

    date = fields.Date(string='Date')
    description = fields.Char(string="Description")
    day = fields.Char(string='Day', compute='_get_day')
    year_id = fields.Many2one('yearly.holidays', string='Year', ondelete='cascade')

    @api.depends('date')
    def _get_day(self):
        """
        Method to get the the
        name of week day
        """
        for date in self:
            day = ''
            if date.date:
                date_obj = date.date
                day = calendar.day_name[date_obj.weekday()]
            date.day = day

    @api.constrains('date')
    def check_year(self):
        for record in self:
            if record.date and str(record.date).split('-')[0] != record.year_id.name:
                raise ValidationError(_('Holiday %s does not belong to this year.' % (record.date)))


#TODO   Add the odoo_fbprophet.prophet.bridge model after migration of stock_order point enhancement.






# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
