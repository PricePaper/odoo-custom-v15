"""
@author: Emipro Technologies Pvt. Ltd.
"""
# -*- coding: utf-8 -*-

from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSale
from odoo.http import request
from odoo import http


class ProductHotspot(WebsiteSale):
    """
    Class for product hotspot handling
    """

    # Render the Hotspot configuration popup
    @http.route('/get-image-hotspot-template', type='json', auth='public', website=True)
    def get_image_hotspot_template(self, **kw):
        """
        Render template for Hotspot configuration
        @param kw: -
        @return: template
        """
        tmplt = request.env['ir.ui.view'].sudo().search(
            [('key', '=', 'emipro_theme_base.image_hotspot_configure_template')])
        if tmplt:
            response = http.Response(template='emipro_theme_base.image_hotspot_configure_template')
            return response.render()

    # Render the Product List
    @http.route('/get-suggested-products-for-hotspot', type='json', auth='public', website=True)
    def get_suggested_products_for_hotspot(self, **kw):
        """
        Render the Product List
        @param kw: deict for product
        @return: rec of 'product.template'
        """
        key = kw.get('key')
        website_domain = request.website.website_domain()
        products = request.env['product.template'].search(
            [('sale_ok', '=', True), ('name', 'ilike', key), ('type', 'in', ['product', 'consu'])] +
            website_domain, limit=5)
        tmplt = request.env['ir.ui.view'].sudo().search(
            [('key', '=', 'emipro_theme_base.suggested_products_for_hotspot')])
        if tmplt:
            response = http.Response(template='emipro_theme_base.suggested_products_for_hotspot',
                                     qcontext={'products': products})
            return response.render()
        return products

    # Render the Hotspot Product popover template
    @http.route('/get-pop-up-product-details', type='json', auth='public', website=True)
    def get_popup_product_details(self, **kw):
        """
        Render the Hotspot Product popover template
        @param kw: dict for product details
        @return: response for template
        """
        product = kw.get('product')
        if product:
            product = request.env['product.template'].sudo().browse(product)
            response = http.Response(template='emipro_theme_base.product_add_to_cart_popover',
                                     qcontext={'product': product})
            return response.render()
