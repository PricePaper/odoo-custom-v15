# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_is_zero, float_round
from datetime import datetime, date
from odoo.http import request
from odoo import tools,_
import logging
_logger = logging.getLogger(__name__)

class WebsiteSale(WebsiteSale):

    @http.route('/get/uom/price',type='json', auth='public', website=True)
    def get_uom_price(self,uom_id,product_id):
        product = request.env['product.product'].browse([int(product_id)])
        product_uom = request.env['uom.uom'].browse([int(uom_id)])
        msg, product_price, price_from = self.get_product_price(product,product_uom)
        return{
            'new_price':product_price
        }


    def get_product_price(self,product_id,product_uom):
           
        """
        Fetch unit price from the relevant pricelist of partner
        if product is not found in any pricelis_uot,set
        product price as Standard price of product
        """
        prices_all = request.env['customer.product.price']
        for rec in request.env.user.partner_id.customer_pricelist_ids:
            if not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= date.today():
                prices_all |= rec.pricelist_id.customer_product_price_ids

        prices_all = prices_all.filtered(
            lambda r: r.product_id.id == product_id.id and r.product_uom.id == product_uom.id and (
                    not r.partner_id or r.partner_id.id == request.env.user.partner_id.id))
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


    def _prepare_product_values(self, product, category, search, **kwargs):
        res = super(WebsiteSale,self)._prepare_product_values(product=product,category=category,search=search,**kwargs)
        # import pdb
        # pdb.set_trace()
        msg,product_price,price_form = self.get_product_price(product.product_variant_ids[0],product.product_variant_ids[0].sale_uoms[0])
        _logger.info(f"================================={[msg,product_price,price_form]}")

        res.update(
            new_price =product_price,
            sale_uoms = product.product_variant_ids[0].sale_uoms,
            price_msg = msg
        )

        return res