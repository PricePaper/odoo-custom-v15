# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime

class CustomerProductPrice(models.Model):
    _inherit = 'customer.product.price'


    customer_rank = fields.Char(string='Customer Rank', related='partner_id.rnk_lst_3_mon', readonly=True)
    mrg_per_lst_3_mon = fields.Float(string='Profit Margin %', related='partner_id.mrg_per_lst_3_mon', readonly=True)
    last_sale_date = fields.Datetime(compute='_get_last_sale_details', string='Last Sale', readonly=True)
    last_sale_price = fields.Float(compute='_get_last_sale_details', string='Last Sale Price', readonly=True)
    last_quantity_sold = fields.Float(compute='_get_last_sale_details', string='Last Sale Qty', readonly=True)
    is_taxable = fields.Boolean(compute='_get_last_sale_details', string='Is Taxable', readonly=True)
    median_price = fields.Html(string='Median Prices', related='product_id.median_price', readonly=True)
    competietor_price_ids = fields.Many2many('customer.product.price', compute="_get_competietor_prices", string='Competietor Price Entries')
    std_price = fields.Float(string='Standard Price', related='product_id.lst_price', readonly=True)
    deviation = fields.Integer(string='Deviation%', compute="get_deviation", readonly=True)

    @api.depends('price','std_price')
    def get_deviation(self):
        for line in self:
            if line.std_price != 0.0:
                line.deviation = (line.price - line.std_price) * 100 / line.std_price

    @api.multi
    def _get_competietor_prices(self):
        for line in self:
            comp_lines = self.search([('pricelist_id.type', '=', 'competitor'), ('product_id', '=', line.product_id.id)])
            line.competietor_price_ids = [l.id for l in comp_lines]

    @api.depends('partner_id', 'product_id')
    def _get_last_sale_details(self):
        for record in self:
            res = {}
            pr_id = record.product_id.id
            if not isinstance(pr_id, int):
                record_read = record.search_read([('id', '=', record.id)], ['product_id'])
                pr_id = record_read and record_read[0].get('product_id', ()) and record_read[0].get('product_id', ())[0]
            if record.pricelist_id.type != 'customer':
                continue
            if record.partner_id and pr_id:
                res = self.env['sale.history'].search([('product_id', '=', pr_id), ('partner_id', '=', record.partner_id.id)])
                if res:
                    record.last_sale_date = res.order_date
                    record.last_sale_price = res.order_line_id.price_unit
                    record.last_quantity_sold = res.order_line_id.product_uom_qty
                tax_res = self.env['sale.tax.history'].search([('product_id', '=', pr_id), ('partner_id', '=', record.partner_id.id)])
                if tax_res and tax_res.tax:
                    record.is_taxable = True
                else:
                    record.is_taxable = False

    @api.multi
    def action_remove(self):
        self.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            }




CustomerProductPrice()
