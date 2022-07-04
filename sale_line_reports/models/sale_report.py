# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    sales_persons = fields.Text('Associated Salesperson')

    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        fields['sales_persons'] = ", array_to_string(array_agg(distinct c.name),'|') as sales_persons"
        return super(SaleReport, self)._select_sale(fields)

    def _from_sale(self, from_clause=''):
        if from_clause:
            from_clause = "%s join res_partner_sale_order_rel a on a.sale_order_id = s.id join res_partner c on a.res_partner_id = c.id" % from_clause
        else:
            from_clause = " join res_partner_sale_order_rel a on a.sale_order_id = s.id join res_partner c on a.res_partner_id = c.id"
        return super(SaleReport, self)._from_sale(from_clause)
