# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    sales_persons = fields.Text('Associated Salesperson')

    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        fields['sales_persons'] = ", array_to_string(array_agg(distinct srp.name),'  |  ') as sales_persons"
        return super(SaleReport, self)._select_sale(fields)

    def _from_sale(self, from_clause=''):
        if from_clause:
            from_clause = """%s join res_partner_sale_order_rel salesperson on salesperson.sale_order_id = s.id
                          join res_partner srp on salesperson.res_partner_id = srp.id""" % from_clause
        else:
            from_clause = """ join res_partner_sale_order_rel salesperson on salesperson.sale_order_id = s.id
                        join res_partner srp on salesperson.res_partner_id = srp.id"""
        return super(SaleReport, self)._from_sale(from_clause)
