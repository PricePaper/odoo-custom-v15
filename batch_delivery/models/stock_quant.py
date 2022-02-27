# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        product_id = self.product_id
        location_src = product_id and product_id.property_stock_location and \
                       product_id.property_stock_location.id or product_id and \
                       product_id.categ_id and product_id.categ_id.property_stock_location and \
                       product_id.categ_id.property_stock_location.id or False
        if self.product_id.tracking in ['lot', 'serial']:
            previous_quants = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id.usage', 'in', ['internal', 'transit'])], limit=1, order='create_date desc')
            if previous_quants:
                self.location_id = previous_quants.location_id
        if not self.location_id:
            company_id = self.company_id and self.company_id.id or self.env.company.id
            if location_src and not product_id.qty_available:
                self.location_id = location_src
            else:
                self.location_id = self.env['stock.warehouse'].search(
                    [('company_id', '=', company_id)], limit=1).in_type_id.default_location_dest_id

