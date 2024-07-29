# -*- coding: utf-8 -*-


from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_is_zero, float_round

from odoo.http import request

class Product(models.Model):
    _inherit = 'product.product'

    partner_product_names = fields.One2many('partner.product.name', 'product_id', string="Partner Defined Product Names")





    def get_product_price(self,product_id,product_uom):
           
        """
        Fetch unit price from the relevant pricelist of partner
        if product is not found in any pricelis_uot,set
        product price as Standard price of product
        """
        if not request.env.user._is_public():
            curr_comapny = request.session.get('current_website_company')
        else:
            curr_comapny = request.env.user.partner_id.id
        partner_com = request.env['res.partner'].sudo().browse(curr_comapny)
        prices_all = request.env['customer.product.price']
        for rec in partner_com.customer_pricelist_ids:
            if not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= date.today():
                prices_all |= rec.pricelist_id.customer_product_price_ids

        prices_all = prices_all.filtered(
            lambda r: r.product_id.id == product_id.id and r.product_uom.id == product_uom.id and (
                    not r.partner_id or r.partner_id.id == partner_com.id))
        product_price = 0.0
        price_from = False
        msg = ''
        for price_rec in prices_all:

            if price_rec.pricelist_id.type == 'customer' and not price_rec.partner_id and prices_all.filtered(
                    lambda r: r.partner_id):
                continue

            if price_rec.pricelist_id.type not in ('customer', 'shared'):
                msg = "Unit price of this product is fetched from the pricelist %s." % (price_rec.pricelist_id.name)
            product_price = price_rec.price
            price_from = price_rec.id
            break
        if not price_from:
            if product_id and product_uom:
                uom_price = product_id.uom_standard_prices.filtered(lambda r: r.uom_id == product_uom)
                if uom_price:
                    product_price = uom_price[0].price

            msg = "Unit Price for this product is not found in any pricelists, fetching the unit price as product standard price."

       
        product_price = float_round(product_price, precision_digits=2)
        return msg, product_price, price_from





    def get_product_price_sheet(self,uom_id):
        product_uom = self.env['uom.uom'].browse([int(uom_id)])
        msg, product_price, price_from = self.get_product_price(self,product_uom)
        return product_price


class PartnerProductName(models.Model):
    _name = 'partner.product.name'
    _description = 'Partner custom product name'

    _sql_constraints = [('partner_id', 'unique(partner_id, product_id)', 'Each partner can only have one record.')]

    name = fields.Char('Product Name')
    partner_id = fields.Many2one('res.partner', string="Partner")
    product_id = fields.Many2one('product.product', string="Product")



