# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import ValidationError


class ReportDeviatedCost(models.AbstractModel):
    _name = 'report.deviated_cost_sale_report.deviated_cost_report'
    _description = 'Deviated cost sale report'

    def get_sale_order_lines(self, data):
        res = []
        domain = [('state', '=', 'sale'), ('date_order', '>=', data.get('from_date')),
                  ('date_order', '<=', data.get('to_date'))]
        sale_orders = self.env['sale.order'].search(domain)

        order_lines = sale_orders.mapped('order_line').filtered(
            lambda rec: rec.vendor_id and rec.vendor_id.id and rec.rebate_contract_id and rec.rebate_contract_id.id).sorted(
            key=lambda l: (l.vendor_id.id, l.rebate_contract_id.id))
        if data.get('vendor_id'):
            order_lines = order_lines.filtered(lambda rec: rec.vendor_id.id == data.get('vendor_id'))
        if not order_lines:
            raise ValidationError(_('No records available'))
        line_dict = {}

        for line in order_lines:

            line_dict = {
                'so_number': line.order_id.name,
                'date': line.order_id.date_order,
                'product': "[%s]%s" % (line.product_id.default_code, line.product_id.name),
                'qty': line.product_uom_qty,
                'unit_cost_purchased': line.product_cost and line.product_cost or False,
                'unit_cost_sold': line.working_cost,
                'deviated_cost': line.product_cost and
                line.product_uom_qty * (line.product_cost - line.working_cost) or False
            }
            con_line = {'contract_id': line.rebate_contract_id,
                        'lines': [line_dict]
                        }
            if res and res[-1].get('vendor_id', False) == line.vendor_id.id:
                if res[-1]['order_lines'] and res[-1]['order_lines'][-1].get('contract_id',
                                                                             False) == line.rebate_contract_id:
                    res[-1]['order_lines'][-1].get('lines').append(line_dict)
                else:
                    res[-1]['order_lines'].append(con_line)
            else:
                vals = {
                    'vendor_id': line.vendor_id.id,
                    'vendor_name': line.vendor_id.name,
                    'order_lines': [con_line],
                }
                res.append(vals)

        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_model': 'sale.order',
            'docs': self.env['account.move'],
            'data': data,
            'orders': self.get_sale_order_lines(data)
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
