import datetime
from datetime import timedelta
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSale
from odoo.http import request
from odoo import http, _
from odoo.tools.safe_eval import safe_eval


class SliderBuilder(WebsiteSale):

    # Render the product list
    @http.route(['/get-product-list'], type='json', auth="public", website=True)
    def get_product_listing(self, name=False, **kwargs):
        """
        Render the product list
        @param name: product slider name
        @param kwargs: get related key value pairs
        @return: response
        """
        products = filters = error = error_msg = False
        limit = kwargs.get('limit')
        if name:
            if name == 'new-arrival':
                products = self.new_arrival_products(20)
            elif name == 'best-seller':
                products = self.best_seller_products(20)
            elif name == 'product-discount':
                products = self.discounted_products('product', [20])
            elif name == 'product-category-discount':
                products = self.discounted_products('category', request.website.category_check().ids,
                                                    discount_policy='product', limit=20)
            elif name == 'custom-domain':
                filters = request.env['slider.filter'].sudo().search(
                    [('website_published', '=', True), ('filter_domain', '!=', False)])
            elif name == 'manual-configuration':
                products = request.env['product.template'].sudo().search([], limit=2)
        if not (products or filters):
            error_msg = _("ERROR MESSAGE WILL BE DISPLAYED HERE")
        response = http.Response(template='emipro_theme_base.product_display_prod_template',
                                 qcontext={'name': name, 'limit': limit, 'products': products, 'filters': filters,
                                           'error': error, 'error_msg': error_msg})
        return {'template_data': response.render(), 'error': error, 'error_msg': error_msg}

    # Render the the selected products while edit the manual configuration slider
    @http.route('/get-products-of-slider', type='json', auth='public', website=True)
    def get_products_of_slider(self, **kw):
        """
        Render the the selected products while edit the manual configuration slider
        @param kw: dict for product ids
        @return: http response
        """
        product_ids = kw.get('item_ids')
        if product_ids:
            products = request.env['product.template'].sudo().search([('id', 'in', product_ids), ('sale_ok', '=', True),
                                                                      ('website_published', '=', True),
                                                                      ('type', 'in', ['product', 'consu']),
                                                                      ('website_id', 'in',
                                                                       [False, str(request.website.id)])])
            response = http.Response(template='emipro_theme_base.edit_product_template',
                                     qcontext={'products': products})
            return response.render()

    @http.route('/load-more-category-brand', type='json', auth='public', website=True)
    def load_more_category_brand(self, **kw):
        """
        category/brand slider render
        @param kw: dict to get slider details
        @return: http response
        """
        name = kw.get('name')
        loaded_items = int(kw.get('loaded_items', False))
        item_ids = self.get_item_ids(kw.get('item_ids', []),'int')
        response = False
        items, items_count = self.get_category_brand(name=name) if loaded_items and name else False
        items = (items - items.filtered(lambda r: r.id not in item_ids)) + items.filtered(
            lambda r: r.id not in item_ids) if item_ids else items
        items = items[loaded_items:loaded_items + 20]
        if items:
            tmplt = request.env['ir.ui.view'].sudo().search(
                [('key', '=', 'emipro_theme_base.brand_category_configure_template')])
            if tmplt:
                response = http.Response(template='emipro_theme_base.list_items',
                                         qcontext={'items': items, 'name': name})
        return {'response': response.render() if response else False, 'items_count': items_count,
                'loaded_items': loaded_items + len(items) if items else loaded_items if loaded_items else 20}

    # Render Category or Brand and it's count
    def get_category_brand(self, name, item_ids=[]):
        """
        Render Category or Brand and it's count
        @param name: category / brand name
        @param item_ids: id for record
        @return: product and counts
        """
        if name == 'category-slider':
            domain = [('website_id', 'in', [False, request.website.id]), ('image_1920', '!=', False)]
            if item_ids:
                domain.append(('id', 'in', item_ids))
            pub_categ_obj = request.env['product.public.category']
            items = pub_categ_obj.sudo().search(domain, order='id desc')
            items_count = pub_categ_obj.sudo().search_count([('website_id', 'in', [False, request.website.id]),
                                                             ('image_1920', '!=', False)])
        else:
            domain = [('website_id', 'in', [False, request.website.id]), ('logo', '!=', False),
                      ('website_published', '=', True)]
            if item_ids:
                domain.append(('id', 'in', item_ids))
            brand_obj = request.env['product.brand.ept']
            items = brand_obj.sudo().search(domain, order='id desc')
            items_count = brand_obj.sudo().search_count([('website_published', '=', True),
                                                         ('website_id', 'in', [False, request.website.id]),
                                                         ('logo', '!=', False)])
        return items, items_count

    # Render Slider Popup
    @http.route('/get-slider-builder-popup', type='json', auth='public', website=True)
    def get_brand_category_template(self, **kw):
        """
        Render Slider Popup
        @param kw: dict to get details
        @return: http response
        """
        name = kw.get('name')
        exclude = kw.get('exclude', False)
        if name in ['category-slider', 'brand-slider']:
            tmplt = request.env['ir.ui.view'].sudo().search(
                [('key', '=', 'emipro_theme_base.brand_category_configure_template')])
            if tmplt:
                item_ids = self.get_item_ids(kw.get('item_ids', []), 'int')
                items, items_count = self.get_category_brand(name, item_ids=item_ids)
                items = items[:20]
                loaded_items = len(item_ids) if item_ids else 20
                slider_type = 'category' if name == 'category-slider' else 'brand'
                styles = request.env['slider.styles'].search(
                    [('slider_type', '=', slider_type), ('style_template_key', '!=', False)])
                limit = kw.get('limit')
                values = {
                    'name': name,
                    'items': items,
                    'items_count': items_count,
                    'limit': limit,
                    'styles': styles,
                    'exclude': exclude,
                    'loaded_items': loaded_items,
                    'available_slider_style': list(set(styles.mapped('slider_style')))
                }
                response = http.Response(template='emipro_theme_base.brand_category_configure_template',
                                         qcontext=values)
                return response.render()
        else:
            tmplt = request.env['ir.ui.view'].sudo().search(
                [('key', '=', 'emipro_theme_base.product_configure_template')])
            filters = request.env['slider.filter'].sudo().search(
                [('website_published', '=', True), ('filter_domain', '!=', False)])
            styles = request.env['slider.styles'].search(
                [('slider_type', '=', 'product'), ('style_template_key', '!=', False)])
            if tmplt:
                values = {
                    'name': name,
                    'filters': filters,
                    'styles': styles,
                    'exclude': exclude,
                    'available_slider_style': list(set(styles.mapped('slider_style')))
                }
                response = http.Response(template='emipro_theme_base.product_configure_template',
                                         qcontext=values)
                return response.render()

    # Render Suggested Product
    @http.route('/get-suggested-products', type='json', auth='public', website=True)
    def get_suggested_products(self, **kw):
        """
        Render Suggested Product
        @param kw: dict to get details
        @return: http response
        """
        tmplt = request.env['ir.ui.view'].sudo().search([('key', '=', 'emipro_theme_base.suggested_products')])
        if tmplt:
            key = kw.get('key')
            exclude_products = kw.get('exclude_products')
            website_domain = request.website.website_domain()
            products = request.env['product.template'].search(
                [('id', 'not in', exclude_products), ('sale_ok', '=', True), ('name', 'ilike', key),
                 ('type', 'in', ['product', 'consu']), ('website_published', '=', True)] + website_domain,
                limit=10)
            response = http.Response(template='emipro_theme_base.suggested_products', qcontext={'products': products})
            return response.render()

    # Render the category And brand slider
    @http.route(['/slider/category-brand-render'], type='json', auth="public", website=True)
    def category_brand_render(self, **kwargs):
        """
        Render the category And brand slider
        @param kwargs: dict for item_ids
        @return: http response
        """
        name = kwargs.get('name', False)
        item_ids = self.get_item_ids(kwargs.get('item_ids', []), 'int')
        if item_ids and name:
            sort_by = kwargs.get('sort_by', 'name asc')
            limit = int(kwargs.get('limit', 10))
            if name == 'brand-slider':
                items = request.env['product.brand.ept'].search([('id', 'in', item_ids),
                                                                 ('website_id', 'in', [False, request.website.id]),
                                                                 ('website_published', '=', True),
                                                                 ('logo', '=', True)], limit=limit, order=sort_by)
            else:
                items = request.env['product.public.category'].search([('id', 'in', item_ids),
                                                                       ('image_1920', '=', True),
                                                                       ('website_id', 'in',
                                                                        [False, request.website.id])],
                                                                      limit=limit, order=sort_by)
            style = int(kwargs.get('style', 0))
            if style:
                slider_style = request.env['slider.styles'].sudo().browse(style).filtered(lambda r: r.exists())
                if items and slider_style:
                    display_product_count = True if kwargs.get('product_count') and kwargs.get('product_count') == '1' else False
                    template_key = f"{request.website.sudo().theme_id.name}.{slider_style.style_template_key}"
                    if request.env['ir.ui.view'].sudo().search([('key', '=', template_key)]):
                        response = http.Response(template=template_key,
                                                 qcontext={"items": items,
                                                           'display_product_count': display_product_count})
                        return response.render()
        if request.env['ir.ui.view'].sudo().search(
                [('key', '=', request.website.sudo().theme_id.name + '.' + 'slider_error_message')]):
            response = http.Response(template=f"{request.website.sudo().theme_id.name}.slider_error_message")
            return response.render()

    # Render The Product Slider
    @http.route(['/slider/render'], type='json', auth="public", website=True)
    def slider_data(self, **kwargs):
        """
        Render The Product Slider
        @param kwargs: dict to get details
        @return: http response
        """
        slider_style_template = int(kwargs.get('style', 0))
        name = kwargs.get('name', False)
        theme_name = request.website.sudo().theme_id.name
        if name and slider_style_template:
            slider_style = request.env['slider.styles'].sudo().search([('id', 'in', [slider_style_template])])
            limit = int(kwargs.get('limit', 10))
            item_ids = self.get_item_ids(kwargs.get('item_ids', []), 'int')
            products = []
            if name == 'manual-configuration' and item_ids:
                products = request.env['product.template'].sudo().search([('id', 'in', item_ids),
                                                                          ('sale_ok', '=', True),
                                                                          ('website_published', '=', True),
                                                                          ('website_id', 'in',
                                                                           [False, request.website.id]),
                                                                          ('type', 'in', ['product', 'consu'])],
                                                                         limit=limit)
            elif name == 'new-arrival':
                products = self.new_arrival_products(limit)
            elif name == 'custom-domain':
                sort_by = kwargs.get('sort_by', 'name asc')
                products = self.custom_domain_products(item_ids, limit, sort_by)
            elif name == 'best-seller':
                products = self.best_seller_products(limit)
            elif name == 'product-discount':
                products = self.discounted_products('product', limit=limit)
            elif name == 'product-category-discount' and item_ids:
                discount_policy = kwargs.get('discount_policy', '')
                products = self.discounted_products('category', item_ids, discount_policy, limit)
            if products and slider_style:
                template_key = f"{theme_name}.{slider_style.style_template_key}"
                if request.env['ir.ui.view'].sudo().search([('key', '=', template_key)]):
                    selected_ui_options = self.get_item_ids(kwargs.get('ui_options', []))
                    response = http.Response(template=template_key,
                                             qcontext={'option': selected_ui_options or [],
                                                       'filter_data': products[:limit]})
                    return response.render()
        if request.env['ir.ui.view'].sudo().search([('key', '=', f"{theme_name}.slider_error_message")]):
            response = http.Response(template=f"{theme_name}.slider_error_message")
            return response.render()

    # Render the custom domain products
    def custom_domain_products(self, filter_id, limit=20, sort_by='name asc'):
        """
        Render the custom domain products
        @param filter_id: filter_id
        @param limit: record limit
        @param sort_by: sort by option
        @return: product records
        """
        if filter_id:
            slider_filter = request.env['slider.filter'].sudo().browse(filter_id[0]).filtered(lambda r: r.exists())
            if slider_filter and slider_filter.website_published:
                domain = safe_eval(slider_filter.filter_domain)
                domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                           ('website_published', '=', True), ('type', 'in', ['product', 'consu']),
                           ('sale_ok', '=', True)]
                return request.env['product.template'].sudo().search(domain, limit=limit, order=sort_by)
        return False

    # Render the new arrival products
    def new_arrival_products(self, limit=10):
        """
        Render the new arrival products
        @param limit: record limit
        @return: product records
        """
        domain = request.website.sale_product_domain()
        domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                   ('website_published', '=', True), ('type', 'in', ['product', 'consu'])]
        return request.env['product.template'].sudo().search(domain, limit=limit, order='id desc')

    # Render the best seller products
    def best_seller_products(self, limit=10):
        """
        Render the best seller products
        @param limit: record limit
        @return: product records
        """
        website_id = request.website.id
        today = datetime.datetime.today()
        request.env.cr.execute(f"""SELECT sr.product_tmpl_id
                                FROM sale_report sr
                                JOIN product_template pt on pt.id = sr.product_tmpl_id 
                                WHERE sr.website_id = {website_id} AND pt.is_published = true 
                                AND (pt.website_id is null or pt.website_id = {website_id})
                                AND pt.sale_ok = true AND pt.type != 'service' AND sr.state in ('sale','done') 
                                AND sr.date BETWEEN '{today - timedelta(30)}' and '{today}' limit {limit}""")
        products_ids = set([x[0] for x in request.env.cr.fetchall()])
        products = request.env['product.template'].sudo().browse(products_ids)
        return products

    # Return Category product or category discount product
    def discounted_products(self, applied_on='', category_ids=[], discount_policy='', limit=10):
        """
        Return Category product or category discount product
        @param applied_on: product or category
        @param category_ids: category_id
        @param discount_policy: policy
        @param limit: record limit
        @return: product records
        """
        price_list = request.website.get_current_pricelist()
        pl_items = price_list.item_ids.filtered(lambda r: r.applied_on == '1_product' and (
                (not r.date_start or r.date_start <= datetime.datetime.today()) and (
                not r.date_end or r.date_end > datetime.datetime.today())))
        if applied_on == 'product':
            return pl_items.mapped('product_tmpl_id').filtered(
                lambda r: r.sale_ok and r.website_published and r.website_id.id in (
                False, request.website.id) and r.type in ['product', 'consu'])[:limit]
        elif category_ids and applied_on == 'category' and discount_policy == 'discounts':
            return pl_items.mapped('product_tmpl_id').filtered(
                lambda r: r.sale_ok and r.website_published and r.website_id.id in (
                False, request.website.id) and r.type in ['product', 'consu'] and [i for i in category_ids if
                                                                                   i in r.public_categ_ids.ids])[:limit]
        else:
            domain = request.website.sale_product_domain()
            domain += ['|', ('website_id', '=', None), ('website_id', '=', request.website.id),
                       ('website_published', '=', True), ('public_categ_ids', 'in', category_ids),
                       ('type', 'in', ['product', 'consu'])]
            return request.env['product.template'].sudo().search(domain, limit=limit)

    def get_item_ids(self,ids,type=None):
        item_ids = []
        if ids and isinstance(ids, str):
            item_ids = [int(i) if type and type == 'int' else i for i in ids.split(',')]
        elif ids:
            item_ids = [int(i) if type and type == 'int' else i for i in ids]
        return item_ids