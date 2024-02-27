# -*- coding: utf-8 -*-

import calendar
import logging as server_log
from datetime import datetime

from dateutil.easter import easter
from dateutil.relativedelta import *

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

try:
    import pandas as pd
    #    import numpy as np
    from prophet import Prophet
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


class ProphetBridge(models.AbstractModel):
    _name = 'odoo_fbprophet.prophet.bridge'
    _description = 'ODOO FBProphet Bridge'

    @api.model
    def remove_non_shipping_days_from_dataframe(self, dataframe):
        """
        removes non-shipping days from the provided dataset
        """
        del_list = []
        for index, row in dataframe.iterrows():
            date = datetime.strptime(str(row['ds']), '%Y-%m-%d %H:%M:%S').date()
            if date.weekday() in (4, 5):
                del_list.append(index)
        dataframe.drop(dataframe.index[del_list], inplace=True)
        return dataframe

    @api.model
    def create_prophet_object(self, date_from, date_to, config=False):
        holidays = self.get_holidays_list(date_from, date_to)  # get holidays in a format conditioned for prophet.

        kwargs = {}

        kwargs.update({'holidays': holidays})

        if config:
            if config.changepoints:
                changepoints = []
                for changepoint in config.changepoints:
                    changepoints.append(changepoint.date)
                kwargs.update({'changepoints': changepoints})

            config.growth and kwargs.update({'growth': config.growth})
            config.n_changepoints and kwargs.update({'n_changepoints': config.n_changepoints})

            ref = {'1': True, '0': False, 'auto': 'auto'}
            config.yearly_seasonality and kwargs.update({'yearly_seasonality': ref.get(config.yearly_seasonality)})
            config.weekly_seasonality and kwargs.update({'weekly_seasonality': ref.get(config.weekly_seasonality)})
            config.daily_seasonality and kwargs.update({'daily_seasonality': ref.get(config.daily_seasonality)})

            config.seasonality_prior_scale and kwargs.update(
                {'seasonality_prior_scale': config.seasonality_prior_scale})
            config.holidays_prior_scale and kwargs.update({'holidays_prior_scale': config.holidays_prior_scale})
            config.changepoint_prior_scale and kwargs.update(
                {'changepoint_prior_scale': config.changepoint_prior_scale})
            config.mcmc_samples and kwargs.update({'mcmc_samples': config.mcmc_samples})
            config.interval_width and kwargs.update({'interval_width': config.interval_width})
            config.uncertainty_samples and kwargs.update({'uncertainty_samples': config.uncertainty_samples})
            # kwargs.update({'monthly_seasonality': True})
        # print('\n\n\n\n',kwargs,'kwargs\n\n\n\n\n')
        prophet_obj = Prophet(**kwargs)  # add all variables and initialise object
        prophet_obj.add_seasonality(name='monthly', period=30.5, fourier_order=5, mode='multiplicative')

        if config and config.quarterly_seasonality == '1':
            prophet_obj.add_seasonality(name='quarterly', period=91.3125, fourier_order=10)
            print("quarterly seasonality applied")

        return prophet_obj

    def months_between_dates(self, end_date, periods):

        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        start_date = end_date - relativedelta(days=periods)

        current_date = start_date
        months_list = []
        # print(current_date, end_date)
        while current_date <= end_date:
            months_list.append(current_date.month)
            current_date += relativedelta(days=30)  # Assuming an average of 30 days per month

        return list(set(months_list))

    def _get_month(self, date_str):
        date_str = datetime.strptime(date_str, '%Y-%m-%d')
        # print(date_str.month)
        return date_str.month



    def is_off_season(self, ds):
        date = pd.to_datetime(ds)


    @api.model
    def run_prophet(self, dataset, date_from, date_to, periods=12, freq='m', config=False):
        """
        the core method that calls the fbprophet forecasting
        date from and date to is used to denotet the holidays
        ranges to be considered. periods and frequency is used
        to set the no of periods and frequency for the forecast
        daily seasonality is a parameter used to tell prophet if
        daily seasonality should be considered instead of monthly
        or weekly
        """
        # print(dataset,date_from, date_to, 12, 'm', config)
        dst = []
        # print(date_from, date_to, periods)
        months = self.months_between_dates(date_to, periods)

        for d in dataset:
            if self._get_month(d[0]) in months:
                dst.append(d)
            # if '01-15' in d[0]:
            #     input(d)
        dataset = dst
        # print(dst)
        # convert the dataset to a pandas dataframe object with fbprophet forced coloumn names df and y
        dataframe = pd.DataFrame(dataset, columns=['ds', 'y'])

        if config and config.growth == 'logistic':  # cap and floor values needs to be set if growth is set as logistic
            dataframe['cap'] = config.dataframe_cap
            dataframe['floor'] = config.dataframe_floor


        m = self.create_prophet_object(date_from, date_to, config=config)
        m.fit(dataframe)  # pass historical dataframe
        future = m.make_future_dataframe(periods=periods, freq=freq)  # make future dataframe
        future = self.remove_non_shipping_days_from_dataframe(future)

        if config and config.growth == 'logistic':  # cap and floor values needs to be set if growth is set as logistic
            future['cap'] = config.dataframe_cap
            future['floor'] = config.dataframe_floor

        forecast = m.predict(future)  # run prophet to predict future
        # for f in  forecast:
        #     print(f, forecast[f])

        forecast['ds'] = pd.to_datetime(forecast['ds']).apply(lambda x: x.date().strftime('%Y-%m-%d'))
        forecast['multiplicative_terms'].clip(lower=0)
        forecast['multiplicative_terms_lower'].clip(lower=0)
        forecast['multiplicative_terms_upper'].clip(lower=0)
        # , 'trend', 'trend_lower', 'trend_upper', 'multiplicative_terms', 'multiplicative_terms_lower', 'multiplicative_terms_upper'
        # convert the result back to list of tuples
        forecast = list(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].itertuples(index=False, name=None))

        return forecast

    @api.model
    def get_holidays_list(self, date_from, date_to):
        """
        Get all the holidays between date_from and to_date
        create a dataframe with the given data
        """

        holidays = self.env['holiday.day'].search([('date', '>=', date_from), ('date', '<=', date_to)])
        if not holidays:
            raise ValidationError(_(
                'Empty holidays list received,Please enter holidays with the path Settings/Technical/Yearly Holidays/Year'))
        holidays = holidays and [h.date for h in holidays] or []
        holidays = pd.DataFrame({
            'holiday': 'Holiday',
            'ds': pd.to_datetime(holidays),
            'lower_window': 0,
            'upper_window': 1,
        })
        return holidays



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
