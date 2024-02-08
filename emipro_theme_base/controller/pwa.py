# -*- coding: utf-8 -*-
import logging
from odoo.http import request, route
from odoo import http

_logger = logging.getLogger(__name__)


class PwaMain(http.Controller):

    def get_asset_urls(self, asset_xml_id):
        """
        get url of the asstes from xml id
        @param asset_xml_id: xml id
        @return: url
        """
        qweb = request.env['ir.qweb'].sudo()
        assets = qweb._get_asset_nodes(asset_xml_id, css=True, js=True)
        urls = []
        for asset in assets:
            if asset[0] == 'link':
                urls.append(asset[1]['href'])
            if asset[0] == 'script':
                urls.append(asset[1]['src'])
        return urls

    @route('/service_worker', type='http', auth="public")
    def service_worker(self):
        """
        get service worker response
        @return: http response
        """
        urls = []
        urls.extend(self.get_asset_urls("web.assets_common"))
        urls.extend(self.get_asset_urls("web.assets_backend"))
        version_list = []
        website_id = request.env['website'].sudo().get_current_website().id
        for url in urls:
            version_list.append(url.split('/')[3])
        cache_version = '-'.join(version_list)
        mimetype = 'text/javascript;charset=utf-8'
        values = {
            'pwa_cache_name': cache_version + '-pwa_cache-' + str(website_id),
            'website_id': website_id,
        }
        content = http.Response(template="emipro_theme_base.service_worker", qcontext=values).render()
        return request.make_response(content, [('Content-Type', mimetype)])

    @route('/pwa_ept/manifest/<int:website_id>', type='http', auth="public", website=True)
    def manifest(self, website_id=None):
        """
        get pwa records
        @param website_id: website_id
        @return: response
        """
        if website_id:
            website = request.env['website'].search([('id', '=', website_id)])
        else:
            website = request.website
        values = self.get_app_image_vals(website)
        values.update({
            'pwa_name': website.pwa_name or 'PWA Website',
            'pwa_short_name': website.pwa_short_name or 'PWA Website',
            'pwa_start_url': website.pwa_start_url or '/',
            'background_color': website.pwa_bg_color or '#dddddd',
            'theme_color': website.pwa_theme_color or '#dddddd',
        })
        content = http.Response(template="emipro_theme_base.manifest", qcontext=values).render()
        return request.make_response(content, [('Content-Type', 'application/json;charset=utf-8')])

    def get_app_image_vals(self, website):
        """
        get link for app images
        @param website: website_id
        @return: dict
        """
        vals = {}
        size_arr = {'app_image_48': '48x48', 'app_image_72': '72x72', 'app_image_96': '96x96',
                    'app_image_144': '144x144', 'app_image_152': '152x152', 'app_image_168': '168x168',
                    'app_image_192': '192x192', 'app_image_256': '256x256', 'app_image_384': '384x384',
                    'app_image_512': '512x512'}
        for x, y in size_arr.items():
            vals.update({x: "/web/image/website/%s/app_image_512/%s" % (website.id, y) if website.app_image_512 else 'emipro_theme_base/static/src/img/%s.png' % (y)})
        return vals
