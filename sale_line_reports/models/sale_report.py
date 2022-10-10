# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime


class SaleReport(models.Model):
    _inherit = "sale.report"

    sales_persons = fields.Text('Associated Salesperson')

    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        fields['sales_persons'] = ", s.sales_person_name as sales_persons"
        return super(SaleReport, self)._select_sale(fields)
    #
    # def _from_sale(self, from_clause=''):
    #     if from_clause:
    #         from_clause = """%s join res_partner_sale_order_rel salesperson on salesperson.sale_order_id = s.id
    #                       join res_partner srp on salesperson.res_partner_id = srp.id""" % from_clause
    #     else:
    #         from_clause = """ join res_partner_sale_order_rel salesperson on salesperson.sale_order_id = s.id
    #                     join res_partner srp on salesperson.res_partner_id = srp.id"""
    #     return super(SaleReport, self)._from_sale(from_clause)

    def _get_fiscal_year(self, date, mode='current'):
        if mode == 'last':
            if int(self.env.user.company_id.fiscalyear_last_month) > date.month:
                start_date = datetime.strptime("%s-%s-%s" % (date.year - 1, int(self.env.user.company_id.fiscalyear_last_month) + 1, 1),
                                               DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.strptime(
                    "%s-%s-%s" % (date.year, int(self.env.user.company_id.fiscalyear_last_month), self.env.user.company_id.fiscalyear_last_day),
                    DEFAULT_SERVER_DATE_FORMAT)
            else:
                start_date = datetime.strptime("%s-%s-%s" % (date.year - 2, int(self.env.user.company_id.fiscalyear_last_month) + 1, 1),
                                               DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.strptime(
                    "%s-%s-%s" % (date.year - 1, self.env.user.company_id.fiscalyear_last_month, self.env.user.company_id.fiscalyear_last_day),
                    DEFAULT_SERVER_DATE_FORMAT)
        else:
            if int(self.env.user.company_id.fiscalyear_last_month) > date.month:
                start_date = datetime.strptime("%s-%s-%s" % (date.year, int(self.env.user.company_id.fiscalyear_last_month) + 1, 1),
                                               DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.strptime(
                    "%s-%s-%s" % (date.year + 1, int(self.env.user.company_id.fiscalyear_last_month), self.env.user.company_id.fiscalyear_last_day),
                    DEFAULT_SERVER_DATE_FORMAT)
            else:
                start_date = datetime.strptime("%s-%s-%s" % (date.year-1, int(self.env.user.company_id.fiscalyear_last_month) + 1, 1),
                                               DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.strptime(
                    "%s-%s-%s" % (date.year , self.env.user.company_id.fiscalyear_last_month, self.env.user.company_id.fiscalyear_last_day),
                    DEFAULT_SERVER_DATE_FORMAT)
        return start_date, end_date

    def get_new_domain(self, domain, dom, new_dom):
        new_domain = []
        for d in domain:
            if d == dom:
                new_domain += new_dom
            else:
                new_domain.append(d)
        return new_domain


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        new_dom = []
        new_domain = domain
        for dom in domain:
            if len(dom) == 3 and dom[0] == 'name' and dom[2] == 'current_fiscal_year':
                start_date, end_date = self._get_fiscal_year(date.today())
                new_dom = ['&', ['date', '>=', start_date], ['date', '<', end_date]]
                new_domain = self.get_new_domain(new_domain, dom, new_dom)
            elif len(dom) == 3 and dom[0] == 'name' and dom[2] == 'last_fiscal_year':
                start_date, end_date = self._get_fiscal_year(date.today(), 'last')
                new_dom = ['&', ['date', '>=', start_date], ['date', '<', end_date]]
                new_domain = self.get_new_domain(new_domain, dom, new_dom)

        if new_dom:
            domain = new_domain
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
