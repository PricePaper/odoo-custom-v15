# -*- coding: utf-8 -*-

import json

import werkzeug.urls
import werkzeug.utils
from datetime import timedelta, date
from odoo.http import request
from odoo.tools import image_process
from werkzeug.exceptions import NotFound
from odoo.tools.safe_eval import safe_eval

import odoo
import logging

from odoo import fields, models, http
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSale
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
from odoo.addons.emipro_theme_base.controller.main import EmiproThemeBaseExtended
from odoo.addons.emipro_theme_base.model import html_dict
_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = "website"

    def _get_default_header_content(self):
        list_obj = html_dict.html.get('default_header_content')
        list_html = ' '.join(['<li>{}</li>'.format(list) for list in list_obj])
        html = """<p></p>
                    <div class="s_rating row te_s_header_offer_text">
                        <ul>{}</ul>
                    </div>""".format(list_html)
        return html

    def _get_default_footer_extra_links(self):
        list_obj = html_dict.html.get('default_footer_extra_links')
        list_html = ' '.join(['<li><section><a href="#">{}</a></section></li>'.format(list) for list in list_obj])
        html = """<section>
                    <div class="te_footer_inline_menu">
                        <ul class="te_footer_inline_menu_t">{}</ul>
                    </div>
                </section>""".format(list_html)
        return html

    def _get_default_footer_content(self):
        list_objs = html_dict.html.get('default_footer_content')
        list_html = ' '.join(['<div class="col-lg-4 col-md-4 col-6"><ul class="te_footer_info_ept">'+''.join(['<section><li><a href="#">'+list+'</a></li></section>' for list in list_obj])+'</ul></div>' for list_obj in list_objs])
        html = """<p></p><div class="row">{}</div>""".format(list_html)
        return html

    def _get_footer_style_3_content(self):
        list_objs = html_dict.html.get('footer_style_3_content')
        html = ''.join(['<p></p><section><div><h4 class="te_footer_menu_info">'+item+'</h4></div></section><div class="row">'+''.join(['<div class="col-lg-6 col-md-6 col-6"><ul class="te_footer_info_ept">'+''.join(['<section><li><a href="#">'+li+'</a></li></section>' for li in list])+'</ul></div>' for list in lists])+'</div>' for item,lists in list_objs.items()])
        return html

    def _get_footer_style_4_content(self):
        list_objs = html_dict.html.get('footer_style_4_content')
        html = '<p></p><div class="row">'+''.join(['<div class="footer-column-2 col-md-3 col-sm-6"><div class="footer_top_title_div"><h5 class="footer-sub-title">'+title+'</h5><span><span class="fa fa-angle-down"></span></span></div><ul class="te_footer_info_ept">'+''.join(['<section><li><a href="#">'+list+'</a></li></section>' for list in lists])+'</ul></div>' for title,lists in list_objs.items()])+'</div>'
        return html

    def _get_footer_style_5_content(self):
        list_objs = html_dict.html.get('footer_style_5_content')
        html = '<p></p><div class="row">'+''.join(['<div class="col-sm-6"><h3 class="te_block_title">'+title[0]+'</h3><a class="te_collapse_icon collapsed" data-toggle="collapse" data-target="#'+title[1]+'"><div class="te_block_title_col">'+title[0]+'</div><i class="fa fa-plus"></i></a><ul class="te_footer_info_ept collapse" id="'+title[1]+'">'+''.join(['<section><li><a href="#">'+list+'</a></li></section>' for list in lists])+'</ul></div>' for title,lists in list_objs.items()])+'</div>'
        return html

    def _get_footer_style_6_content(self):
        list_objs = html_dict.html.get('footer_style_6_content')
        html = '<p></p><div class="row">'+''.join(['<div class="col-sm-6 col-6 '+title[1]+'"><h3 class="te_block_title">'+title[0]+'</h3><ul class="te_footer_info_ept">'+''.join(['<section><li><a href="#">'+list+'</a></li></section>' for list in lists])+'</ul></div>' for title, lists in list_objs.items()])+'</div>'
        return html

    def _get_footer_style_7_content(self):
        list_objs = html_dict.html.get('footer_style_7_content')
        html = '<p></p><div class="row">'+''.join(['<div class="col-md-6 col-6"><h3 class="te_block_title">'+title+'</h3><ul class="te_footer_info_ept">'+''.join(['<section><li><i class="fa fa-long-arrow-right"></i><a href="#">'+list+'</a></li></section>' for list in lists])+'</ul></div>' for title, lists in list_objs.items()])+'</div>'
        return html

    def _get_default_header_extra_links(self):
        list_objs = html_dict.html.get('default_header_extra_links')
        html = '<p></p><div class="te_header_static_menu"><ul>'+''.join(['<li><a href="#">'+title+'</a></li>' for title in list_objs])+'</ul></div>'
        return html

    def _get_default_vertical_menu(self):
        list_objs = html_dict.html.get('default_vertical_menu')
        html = '<section><div class="te_sidenav_menu"><ul>'+''.join(['<section><li><a href="/'+title[0]+'">'+title[1]+'</a></li></section>' for title in list_objs])+'</ul></div><div class="te_sidenav_content"><section><p>Pellentesque mollis nec orci id tincidunt. Sed mollis risus eu nisi aliquet, sit amet fermentum.</p></section></div></section>'
        return html

    is_load_more = fields.Boolean(string='Load More', help="Load more will be enabled", readonly=False)
    load_more_image = fields.Binary('Load More Image', help="Display this image while load more applies.",
                                    readonly=False)
    button_or_scroll = fields.Selection([
        ('automatic', 'Automatic- on page scroll'),
        ('button', 'Button- on click button')
    ], string="Loading type for products",
        required=True, default='automatic', readonly=False)
    prev_button_label = fields.Char(string='Label for the Prev Button', readonly=False,
                                    default="Load prev", translate=True)
    next_button_label = fields.Char(string='Label for the Next Button', readonly=False,
                                    default="Load next", translate=True)
    is_lazy_load = fields.Boolean(string='Lazyload', help="Lazy load will be enabled", readonly=False)
    lazy_load_image = fields.Binary('Lazyload Image', help="Display this image while lazy load applies.",
                                    readonly=False)
    banner_video_url = fields.Many2one('ir.attachment', "Video URL", help='URL of a video for banner.', readonly=False)
    number_of_product_line = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3')
    ], string="Number of lines for product name", default='1', readonly=False, help="Number of lines to show in product name for shop.")
    website_company_info = fields.Text(string="Company Information", translate=True,
                                       default="We are a team of passionate people whose goal is to improve "
                                               "everyone's life through disruptive products. We build great products to solve your business problems.")
    website_footer_extra_links = fields.Html(string="Footer Content", translate=True,
                                             default=_get_default_footer_extra_links)
    website_header_offer_ept = fields.Html(string="Clarico Header Offer Content", translate=True,sanitize=False,
                                           default=_get_default_header_content)
    footer_style_1_content_ept = fields.Html(string="Clarico Footer Style 1 Content", translate=True,sanitize=False,
                                             default=_get_default_footer_content)
    footer_style_3_content_ept = fields.Html(string="Clarico Footer Style 3 Content", translate=True,sanitize=False,
                                             default=_get_footer_style_3_content)
    footer_style_4_content_ept = fields.Html(string="Clarico Footer Style 4 Content", translate=True,sanitize=False,
                                             default=_get_footer_style_4_content)
    footer_style_5_content_ept = fields.Html(string="Clarico Footer Style 5 Content", translate=True,sanitize=False,
                                             default=_get_footer_style_5_content)
    footer_style_6_content_ept = fields.Html(string="Clarico Footer Style 6 Content", translate=True, sanitize=False,
                                             default=_get_footer_style_6_content)
    footer_style_7_content_ept = fields.Html(string="Clarico Footer Style 7 Content", translate=True, sanitize=False,
                                             default=_get_footer_style_7_content)
    website_header_extra_links = fields.Html(string="Clarico Header Extra Content", translate=True, sanitize=False,
                                           default=_get_default_header_extra_links)
    website_vertical_menu_ept = fields.Html(string="Vertical Menu Content", translate=True, sanitize=False,
                                           default=_get_default_vertical_menu)
    is_auto_play = fields.Boolean(string='Slider Auto Play', default=True, readonly=False)

    is_pwa = fields.Boolean(string='PWA', readonly=False, help="Pwa will be enabled.")
    pwa_name = fields.Char(string='Name', readonly=False)
    pwa_short_name = fields.Char(string='Short Name', readonly=False)
    pwa_theme_color = fields.Char(string='Theme Color', readonly=False)
    pwa_bg_color = fields.Char(string='Background Color', readonly=False)
    pwa_start_url = fields.Char(string='Start URL', readonly=False)
    app_image_512 = fields.Binary(string='Application Image(512x512)', readonly=False, store=True)
    is_price_range_filter = fields.Boolean(string='Price Range Filter',help="Enable the price range filter")
    price_filter_on = fields.Selection([
        ('list_price', 'On Product Sale Price'),
        ('website_price', 'On Product Discount Price')
    ], string="Price Range Filter For Products",
         default='list_price', readonly=False)
    option_out_of_stock = fields.Boolean('Out of Stock')
    text_out_of_stock = fields.Char('Text for Out of Stock', default='OUT OF STOCK', translate=True)
    b2b_hide_details = fields.Boolean('Hide Add to Cart')
    text_b2b_hide_details = fields.Char('Text for Details', default='to view price', translate=True)
    is_b2b_message = fields.Boolean('Display Message?')
    b2b_hide_add_to_cart = fields.Boolean('Hide Add to Cart Feature')
    b2b_hide_price = fields.Boolean('Hide Product Price')
    allow_reorder = fields.Boolean(string='Allow Reorder', help='Enable to allow reorder the existing sales orders')
    b2b_checkout = fields.Boolean('Restrict Checkout')
    search_in_brands = fields.Boolean('Search with Brands', default=True)
    search_in_attributes_and_values = fields.Boolean('Search with Attributes', default=True)
    enable_smart_search = fields.Boolean('Advanced Search', default=True)

    def getDatabase(self):
        """
                To display database in login popup
                :return: List of databases
                """
        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        return values['databases']

    def category_check(self):
        """
        To display main parent product.public.category website specific
        :return:
        """
        return self.env['product.public.category'].sudo().search(
            [('parent_id', '=', False), ('website_id', 'in', (False, self.id))])

    def get_default_company_address(self):
        """
        To get company default address
        :return:
        """
        company = request.env['website'].get_current_website().company_id
        values = {}
        for field in ['street', 'street2', 'city', 'zip', 'state_id', 'country_id']:
            if hasattr(company,field) and bool(getattr(company,field)):
                if hasattr(getattr(company,field),'name'):
                    values.update({field: str(getattr(getattr(company,field),'name'))})
                else:
                    values.update({field: str(getattr(company, field))})
        return " ".join([v for v in values.values()])

    def get_carousel_category_list(self):
        """
        This method is used for return the list of category
        which has selected the allow category in carousel option from admin
        :return: list of category.
        """
        return []

    def get_product_categs_path(self, id):
        """
        To render full path for breadcrumbs based on argument
        :param id: product.public.category
        :return: list of category path and website url
        """
        categ_set = []
        categ_name_set = []
        while id:
            categ = self.env['product.public.category'].sudo().search([('id', '=', id)])
            categ_set.append(categ.id)
            categ_name_set.append(categ.name)
            if categ and categ.parent_id:
                id = categ.parent_id.id
            else:
                break

        # For Reverse order
        categ_set = categ_set[::-1]
        categ_name_set = categ_name_set[::-1]

        values = {
            'categ_set': categ_set,
            'categ_name_set':categ_name_set,
            'web_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        }
        return values

    def get_min_max_prices(self, search=False, category=False, attributes=False):
        """
        Get minimum price and maximum price according to Price list as well as discount for Shop page
        :return: min and max price value
        """
        range_list = []
        cust_min_val = request.httprequest.values.get('min_price', False)
        cust_max_val = request.httprequest.values.get('max_price', False)
        domain = WebsiteSaleWishlist._get_search_domain(self, search=search, category=category,
                                                        attrib_values=attributes)

        if attributes:
            ids = [attrib[1] for attrib in attributes if attrib[0] == 0]
            if ids:
                domain += [('product_brand_ept_id.id', 'in', ids)]
        products = self.env['product.template'].search(domain)
        prices_list = []
        min_price = max_price = 0
        is_web_price = request.website.price_filter_on == 'website_price'
        if products:
            pricelist = self.get_current_pricelist()
            if is_web_price:
                context = dict(self.env.context, quantity=1, pricelist=pricelist.id if pricelist else False)
                products = products.with_context(context).sorted('price')
            else:
                products = products.sorted('list_price')
                min_price = products[0].currency_id._convert(products[0].list_price, pricelist.currency_id,
                                                              self.company_id, date=fields.Date.today())
                max_price = products[-1].currency_id._convert(products[-1].list_price, pricelist.currency_id,
                                                              self.company_id, date=fields.Date.today())

        if not products : return False

        try:
            cust_max_val = float(cust_max_val)
        except ValueError:
            cust_max_val = max_price
        try:
            cust_min_val = float(cust_min_val)
        except ValueError:
            cust_min_val = min_price

        if not cust_min_val and not cust_max_val:
            range_list.append(round(products[0].price if is_web_price else min_price,2))
            range_list.append(round(products[-1].price if is_web_price else max_price,2))
            range_list.append(round(products[0].price if is_web_price else min_price, 2))
            range_list.append(round(products[-1].price if is_web_price else max_price, 2))
        else:
            range_list.append(round(float(cust_min_val),2))
            range_list.append(round(float(cust_max_val),2))
            range_list.append(round(products[0].price if is_web_price else min_price, 2))
            range_list.append(round(products[-1].price if is_web_price else max_price, 2))
        return range_list

    def checkQuickFilter(self, currentWebsite, filterWebsiteArray):
        """
        for check functionality for quick filter
        @param currentWebsite: website
        @param filterWebsiteArray: filter data
        @return: Boolean
        """
        if currentWebsite in filterWebsiteArray or len(filterWebsiteArray) == 0:
            return True
        return False

    def list_providers_ept(self):
        """
        This method is used for return the encoded url for the auth providers
        :return: link for the auth providers.
        """
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = OAuthLogin.get_state(self, provider)
            params = dict(
                response_type='token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
        return providers

    def get_shop_products(self, search=False, category=False, attrib_values=False):
        """ Get the product count based on attribute value and current search domain. """
        domain = EmiproThemeBaseExtended._get_search_domain(EmiproThemeBaseExtended(), search, category,
                                                            attrib_values)
        return self._get_filtered_products(domain, False)

    def get_brand_products(self, search=False, category=False, attrib_values=False):
        """ Get the product count based on attribute value and current search domain. """
        domain = EmiproThemeBaseExtended._get_search_domain(EmiproThemeBaseExtended(), search, category,
                                                            attrib_values)
        domain = [dom for dom in domain if not dom[0] == 'product_brand_ept_id.id']
        return self._get_filtered_products(domain, True)

    def _get_filtered_products(self, domain, is_brand=False):
        query = self.env['product.template']._where_calc(domain)
        self.env['product.template']._apply_ir_rules(query, 'read')
        from_clause, where_clause, where_clause_params = query.get_sql()
        where_str = where_clause and ("WHERE %s" % where_clause) or ''

        if is_brand:
            query = f'''select product_brand_ept_id,count(id) as count 
            from product_template 
            where id in (SELECT product_template.id FROM {from_clause} {where_str}) 
            group by product_brand_ept_id'''
        else:
            query = f'''select product_attribute_value_id,count(DISTINCT product_tmpl_id) as count 
            from product_template_attribute_value 
            where ptav_active = true AND product_tmpl_id in (SELECT product_template.id FROM {from_clause} {where_str}) 
            group by product_attribute_value_id'''

        self._cr.execute(query, where_clause_params)

        key = "product_brand_ept_id" if is_brand else "product_attribute_value_id"

        result_dict = {}
        for dict in request.env.cr.dictfetchall():
            result_dict[dict[key]] = dict['count']

        return result_dict

    def get_product_data(self, products, product_count=1):
        product_items = []
        product_data = []
        count = 2
        i = 1
        for product in products:
            product_data.append(product)
            if(count / product_count > i):
                product_items.append(product_data)
                product_data = []
                i += 1
            count += 1
        product_items.append(product_data)
        return product_items

    def _search_with_fuzzy(self, search_type, search, limit, order, options):
        """ to search with all the available synonyms of `search` term,
        only if configuration of search synonyms in website is on.
        """
        curr_website = request.website.get_current_website()
        search_synonyms = False
        count, results, fuzzy_term = 0, [], False
        if search and curr_website.enable_smart_search:
            synonym_groups = request.env['synonym.group'].sudo().search(
                [('website_id', 'in', [curr_website.id, False])])
            if synonym_groups:
                for synonym_group in synonym_groups:
                    synonym_names = synonym_group.name.split(',')
                    synonyms = [synm.strip().lower() for synm in synonym_names]
                    if search.strip().lower() in synonyms:
                        search_synonyms = synonyms
                        break
            if search_synonyms:
                for search_synm in search_synonyms:
                    fuzzy_term = False
                    search_details = self._search_get_details(search_type, order, options)
                    if search_synm and options.get('allowFuzzy', True):
                        fuzzy_term = self._search_find_fuzzy_term(search_details, search_synm)
                        if fuzzy_term:
                            new_count, new_results = self._search_exact(search_details, fuzzy_term, limit, order)
                            if fuzzy_term.lower() == search_synm.lower():
                                fuzzy_term = False
                        else:
                            new_count, new_results = self._search_exact(search_details, search_synm, limit, order)
                    else:
                        new_count, new_results = self._search_exact(search_details, search_synm, limit, order)
                    for new_res in new_results:
                        if new_res not in results:
                            res = [res for res in results if res['model'] == new_res['model']]
                            if res:
                                for prod in new_res['results']:
                                    if prod not in res[0]['results']:
                                        res[0]['results'] += prod
                                        res[0]['count'] += 1
                                        count += 1
                            else:
                                results.append(new_res)
                                count += new_res['count']
            else:
                count, results, fuzzy_term = super(Website, self)._search_with_fuzzy(search_type,
                                                                                     search, limit, order, options)
        else:
            count, results, fuzzy_term = super(Website, self)._search_with_fuzzy(search_type,
                                                                                 search, limit, order, options)
        return count, results, fuzzy_term
