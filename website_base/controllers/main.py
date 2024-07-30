# -*- coding: utf-8 -*-

from odoo import http, _,fields
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_is_zero, float_round
from datetime import datetime, date
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.http import request
from odoo import tools,_
import logging
_logger = logging.getLogger(__name__)

class WebsiteSale(WebsiteSale):


    @http.route()
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page (without redirection).
        """
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=1)
            else:
                return {}
        custom_uom = kw.get('UomProduct')
        if not custom_uom and line_id:
            order_line = request.env['sale.order.line'].browse(line_id)
            custom_uom = order_line.product_uom.id
        pcav = kw.get('product_custom_attribute_values')
        nvav = kw.get('no_variant_attribute_values')
        value = order._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
            no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None,
            custom_uom = custom_uom
        )

        if not order.cart_quantity:
            request.website.sale_reset()
            return value

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity

        if not display:
            return value

        value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': order._cart_accessories()
        })
        value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template("website_sale.short_cart_summary", {
            'website_sale_order': order,
        })
        return value



    def _get_shop_payment_values(self, order, **kwargs):
        res = super(WebsiteSale,self)._get_shop_payment_values(order,**kwargs)
        curr_comapny = request.session.get('current_website_company')
        partner_com = request.env['res.partner'].sudo().browse(curr_comapny)
        res.update(
            tokens = partner_com.payment_token_ids
        )
        return res
        



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



    def _prepare_product_values(self, product, category, search, **kwargs):
        res = super(WebsiteSale,self)._prepare_product_values(product=product,category=category,search=search,**kwargs)
        if product.is_published:
            msg,product_price,price_form = self.get_product_price(product.product_variant_ids[0],product.product_variant_ids[0].sale_uoms[0])
            res.update(
            new_price =product_price,
            sale_uoms = product.product_variant_ids[0].sale_uoms,
            price_msg = msg
        )

        return res
