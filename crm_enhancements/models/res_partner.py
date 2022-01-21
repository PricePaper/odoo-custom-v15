# -*- coding: utf-8 -*-

import calendar
import datetime

from dateutil.relativedelta import *

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    rev_per_trans = fields.Float(string="Revenue Per Transaction")

    business_freq = fields.Selection(selection=[('week', 'Weekly'),
                                                ('biweek', 'Biweekly'),
                                                ('month', 'Monthly')], string="Frequency")
    exp_mon_rev = fields.Float(compute="_calc_expected_revenue", string='Monthly Revenue Expected')

    rev_this_mon = fields.Float(compute="_calc_monthly_revenue", string='Revenue This Month')

    rnk_lst_12_mon = fields.Char(string='Rank Based On Last Year Sales')
    rnk_lst_3_mon = fields.Char(string='Rank Based On Last 3 Month Sales')
    mrg_per_lst_3_mon = fields.Float(string='Profit Margin Percent For The Past 3 Months')

    @api.model
    def set_customer_ranking_cron(self):
        """
        Cron method to Set customer rank based on the Amount configured in Company Record
        """
        last_year_start_date = datetime.datetime.now() - relativedelta(years=1)
        last_year_start_date = datetime.datetime(last_year_start_date.year, last_year_start_date.month, 1)

        last_3_month_start_date = datetime.datetime.now() - relativedelta(months=3)
        last_3_month_start_date = datetime.datetime(last_3_month_start_date.year, last_3_month_start_date.month, 1)


        end_date = datetime.datetime.now() - relativedelta(months=1)
        end_date = datetime.datetime(end_date.year, end_date.month, calendar.mdays[end_date.month], 00, 00, 00)

        last_year_sale_orders = self.env['sale.order'].search(
            [('state', 'in', ['sale', 'done']), ('confirmation_date', '>=', last_year_start_date),
             ('confirmation_date', '<=', end_date)])

        last_3_month_sale_orders = self.env['sale.order'].search(
            [('state', 'in', ['sale', 'done']), ('confirmation_date', '>=', last_3_month_start_date),
             ('confirmation_date', '<=', end_date)])

        for customer in self.env['res.partner'].search([('customer_rank', '>', 0)]):
            customer_last_year_sale_order = last_year_sale_orders.filtered(lambda so: so.partner_id == customer)
            customer_last_3_month_sale_orders = last_3_month_sale_orders.filtered(lambda so: so.partner_id == customer)

            last_year_total = sum(customer_last_year_sale_order.mapped('amount_total'))
            last_3_month_total = sum(customer_last_3_month_sale_orders.mapped('amount_total'))
            profit_margin_lst_3_mnt = sum(customer_last_3_month_sale_orders.mapped('gross_profit'))
            proj_3month_to_one_year = last_3_month_total * 4

            if last_3_month_total:
                customer.mrg_per_lst_3_mon = round(100 * (profit_margin_lst_3_mnt / last_3_month_total), 2)
            if customer.company_id:
                company = customer.company_id
                if last_year_total > company.amount_a:
                    customer.rnk_lst_12_mon = 'A'
                elif last_year_total > company.amount_b:
                    customer.rnk_lst_12_mon = 'B'
                elif last_year_total > company.amount_c:
                    customer.rnk_lst_12_mon = 'C'
                elif last_year_total > company.amount_d:
                    customer.rnk_lst_12_mon = 'D'
                elif last_year_total > company.amount_e:
                    customer.rnk_lst_12_mon = 'E'
                elif last_year_total > company.amount_f:
                    customer.rnk_lst_12_mon = 'F'
                else:
                    customer.rnk_lst_12_mon = 'Z'

                if proj_3month_to_one_year > company.amount_a:
                    customer.rnk_lst_3_mon = 'A'
                elif proj_3month_to_one_year > company.amount_b:
                    customer.rnk_lst_3_mon = 'B'
                elif proj_3month_to_one_year > company.amount_c:
                    customer.rnk_lst_3_mon = 'C'
                elif proj_3month_to_one_year > company.amount_d:
                    customer.rnk_lst_3_mon = 'D'
                elif proj_3month_to_one_year > company.amount_e:
                    customer.rnk_lst_3_mon = 'E'
                elif proj_3month_to_one_year > company.amount_f:
                    customer.rnk_lst_3_mon = 'F'
                else:
                    customer.rnk_lst_3_mon = 'Z'


    @api.depends('sale_order_ids')
    def _calc_monthly_revenue(self):
        """
        this method calculates the current
        months revenue of the current customer
        by seaching his current month sales transactions
        """
        for partner in self:
            orders = self.env['sale.order'].search(
                [('confirmation_date', '!=', False), ('partner_id', 'child_of', partner.id),
                 ('state', 'in', ['sale', 'done'])])
            date_today = datetime.date.today()
            start_date_this_mon, end_date_this_mon = self.get_month_start_end_date(date_today)
            orders_this_month = orders.filtered(
                lambda so: so.confirmation_date > start_date_this_mon and so.confirmation_date < end_date_this_mon)
            partner.rev_this_mon = sum([so.amount_untaxed for so in orders_this_month]) or 0

    @api.model
    def get_month_start_end_date(self, date):
        """
        returns the beginning and ending dates
        of the month of a given date
        """
        start_date = date.replace(day=1)
        end_date = date.replace(day=calendar.monthrange(date.year, date.month)[1])

        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())
        end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time())
        return start_date, end_date

    @api.depends('rev_per_trans', 'business_freq')
    def _calc_expected_revenue(self):
        """
        calculates the expected revenue
        multiplies frequency and revenue
        per transaction
        """
        for partner in self:
            exp_mon_rev = 0.0
            if partner.rev_per_trans and partner.business_freq:
                if partner.business_freq == 'week':
                    exp_mon_rev = partner.rev_per_trans * 4
                elif partner.business_freq == 'biweek':
                    exp_mon_rev = partner.rev_per_trans * 2
                elif partner.business_freq == 'month':
                    exp_mon_rev = partner.rev_per_trans
            partner.exp_mon_rev = exp_mon_rev


    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        """
        mail_post_autofollow=False
        """
        return super(ResPartner, self.with_context(mail_post_autofollow=False)).message_post(**kwargs)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
