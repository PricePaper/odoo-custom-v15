# -*- coding: utf-8 -*-

import calendar
import datetime

from dateutil.relativedelta import *
from odoo.exceptions import UserError

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
            [('state', 'in', ['sale', 'done']), ('date_order', '>=', last_year_start_date),
             ('date_order', '<=', end_date)])

        last_3_month_sale_orders = self.env['sale.order'].search(
            [('state', 'in', ['sale', 'done']), ('date_order', '>=', last_3_month_start_date),
             ('date_order', '<=', end_date)])

        for customer in self.env['res.partner'].search([('customer', '=', True)]):

            customer_last_year_sale_order = last_year_sale_orders.filtered(lambda so: so.partner_id == customer)
            customer_last_3_month_sale_orders = last_3_month_sale_orders.filtered(lambda so: so.partner_id == customer)

            last_year_total = sum(customer_last_year_sale_order.mapped('amount_total'))
            last_3_month_total = sum(customer_last_3_month_sale_orders.mapped('amount_total'))
            profit_margin_lst_3_mnt = sum(customer_last_3_month_sale_orders.mapped('gross_profit'))
            proj_3month_to_one_year = last_3_month_total * 4

            if last_3_month_total:
                customer.mrg_per_lst_3_mon = round(100 * (profit_margin_lst_3_mnt / last_3_month_total), 2)
            if self.env.user.company_id:
                company = self.env.user.company_id
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
            orders = self.env['sale.order'].search([('date_order', '!=', False), ('partner_id', 'child_of', partner.id),
                 ('state', 'in', ['sale', 'done'])])
            date_today = datetime.date.today()
            start_date_this_mon, end_date_this_mon = self.get_month_start_end_date(date_today)
            orders_this_month = orders.filtered(lambda so: so.date_order > start_date_this_mon and so.date_order < end_date_this_mon)
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
    def message_post(self, *,
                     body='', subject=None, message_type='notification',
                     email_from=None, author_id=None, parent_id=False,
                     subtype_xmlid=None, subtype_id=False, partner_ids=None,
                     attachments=None, attachment_ids=None,
                     add_sign=True, record_name=False,
                     **kwargs):
        """
         usually oddo adds the partner as a follower
         we are removing this feature for partner model
        """
        return super(ResPartner, self.with_context(mail_post_autofollow=False)).message_post(
                     body=body, subject=subject, message_type=message_type,
                     email_from=email_from, author_id=author_id, parent_id=parent_id,
                     subtype_xmlid=subtype_xmlid, subtype_id=subtype_id, partner_ids=partner_ids,
                     attachments=attachments, attachment_ids=attachment_ids,
                     add_sign=add_sign, record_name=record_name,
                     **kwargs)

    def create_opportunity(self):
        if self.active:
            raise UserError('Selected partner is not archived.')
        else:
            opportunity = self.env['crm.lead'].create({
                'partner_id': self.id,
                'name': self.name,
                'type': 'opportunity',
                'state_id': 5
            })

            action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
            form_view = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = opportunity.id
            return action





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
