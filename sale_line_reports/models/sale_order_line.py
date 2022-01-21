# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.price_paper.models import margin


class SaleOrderline(models.Model):
    _inherit = 'sale.order.line'

    customer_code = fields.Char(related='order_id.partner_id.customer_code', string='Cust.#')
    date_order = fields.Datetime(related='order_id.date_order', string='Order Date')
    customer_po = fields.Char(related='order_id.client_order_ref', string='Cust P/O#')
    is_taxed = fields.Char(string='TX', compute='_is_taxed')
    cost = fields.Float(string='Cost', related='product_id.cost')
    percent = fields.Float(string='PCT', compute='_calculate_percent')
    class_margin = fields.Float(related='product_id.categ_id.class_margin')
    company_margin = fields.Float(related='company_id.company_margin')
    remark = fields.Char(string='RM', compute='_calculate_remark')
    deliver_by = fields.Date(string="Deliver By", related='order_id.deliver_by')

    def action_view_sale_order(self):
        self.ensure_one()
        if self.order_id.storage_contract:
            view = self.env.ref('price_paper.view_storage_contract_order_form')
        else:
            view = self.env.ref('sale.view_order_form')
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'res_id': self.order_id.id,
            'context': self.env.context,
        }


    def _calculate_percent(self):
        """
        Percentage calculation
        """
        for line in self:
            percent = 0.0
            if line.working_cost:
                percent = margin.get_margin(line.price_unit, line.working_cost, percent=True)
            line.percent = percent

    def _is_taxed(self):
        """
        Tax Line or Not
        """
        for line in self:
            if line.tax_id:
                line.is_taxed = 'T'
            else:
                line.is_taxed = ''

    def _calculate_remark(self):
        """
        Remarks based on conditions
        """
        for line in self:
            remarks = []

            ## TODO move variance percent to company parameters(-->this todo already in 12 code)
            if line.percent < line.class_margin * 0.90:
                remarks.append('CBM')
            elif line.percent > line.class_margin * 1.20:
                remarks.append('CAM')

            if not line.price_unit:
                remarks.append('NC')

            if line.lst_price == line.price_unit:
                remarks.append('FC')

            if line.working_cost == line.price_unit:
                remarks.append('C')
            elif line.working_cost > line.price_unit:
                remarks.append('BC')

            if line.new_product:
                remarks.append('NP')
            if line.manual_price:
                remarks.append('M')

            line.remark = ",".join(remarks)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
