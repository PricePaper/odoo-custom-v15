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

    def checkout_values(self, **kw):
        order = request.website.sale_get_order(force_create=True)
        shippings = []
        if order.partner_id != request.website.user_id.sudo().partner_id:
            Partner = order.partner_id.with_context(show_address=1).sudo()
            shippings = Partner.search([
                ("id", "child_of", order.partner_id.commercial_partner_id.ids),
                '|', ("type", "in", ["delivery", "other"]), ("id", "=", order.partner_id.commercial_partner_id.id)
            ], order='id desc')

            curr_comapny = request.session['current_website_company']
            partner_com = request.env['res.partner'].sudo().browse(curr_comapny)
            access = request.env.user.partner_id.portal_contact_ids.mapped('partner_id')
            # main_ship = partner_com.child_ids
            desired_shipping = shippings.filtered(lambda c: c.id in access.ids or c.id == partner_com.id)
            shippings = desired_shipping
            # print(shippings2)
            print(shippings)
            if shippings:
                if kw.get('partner_id') or 'use_billing' in kw:
                    if 'use_billing' in kw:
                        partner_id = order.partner_id.id
                    else:
                        partner_id = int(kw.get('partner_id'))
                    if partner_id in shippings.mapped('id'):
                        order.partner_shipping_id = partner_id

        values = {
            'order': order,
            'shippings': shippings,
            'only_services': order and order.only_services or False
        }
        return values



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
            curr_comapny = request.session['current_website_company']
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

    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        curr_comapny = request.session.get('current_website_company')
        if not curr_comapny and not request.env.user._is_public():
            return request.redirect('/my/website/company')
        else:
            return super(WebsiteSale,self).product(product, category=category, search=search, **kwargs)

    def _prepare_product_values(self, product, category, search, **kwargs):
        res = super(WebsiteSale,self)._prepare_product_values(product=product,category=category,search=search,**kwargs)
        
        msg,product_price,price_form = self.get_product_price(product.product_variant_ids[0],product.product_variant_ids[0].sale_uoms[0])
        

        res.update(
            new_price =product_price,
            sale_uoms = product.product_variant_ids[0].sale_uoms,
            price_msg = msg
        )

        return res
