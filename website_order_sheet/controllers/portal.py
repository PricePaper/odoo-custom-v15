# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import datetime
from odoo.http import request
from odoo import tools,_
import logging
_logger = logging.getLogger(__name__)

class PortalRequest(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'sheet_count' in counters:
            sheet_count = len(self._prepapare_sheet_domain())
            values['sheet_count'] = sheet_count
        return values
    
    def _prepapare_sheet_domain(self):
        curr_comapny = request.session.get('current_website_company')
        partner = request.env.user.partner_id
        partner_com = False
        if curr_comapny:
            partner_com = request.env['res.partner'].sudo().browse(curr_comapny)

        exising_shipping = partner.portal_contact_ids.partner_id
        desired_shipping = partner_com.child_ids.filtered(lambda c: c.type == 'delivery' and c.id in exising_shipping.ids)
        if desired_shipping and partner_com.child_ids:
            desired_shipping.union((partner_com))
        else:
            desired_shipping = [partner_com]

        return desired_shipping




    @http.route(['/my/order/sheet', '/my/order/sheet/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_requests_test(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        curr_comapny = request.session.get('current_website_company')
        if not curr_comapny:
            return request.redirect('/my/website/company')
        values = self._prepare_portal_layout_values()
        delivery_location = self._prepapare_sheet_domain()
        values.update({
            'delivery_location': delivery_location,
            'page_name': 'order_sheet_locations',
            'default_url': '/my/order/sheet',
        })
        return request.render("website_order_sheet.portal_my_sheet_location", values)
    
    @http.route(['/my/order/sheeet/<int:partner_id>'], type='http', auth="user", methods=['get'], website=True, csrf=False)
    def order_sheet(self,partner_id):
        values = self._prepare_portal_layout_values()
        sheet_id = request.env['website.order.sheet'].sudo().search([('partner_id','=',partner_id)],limit=1)
        partner = request.env['res.partner'].sudo().browse([partner_id])
        main_partner = partner.parent_id.id or partner_id
        # products = self.order_line.mapped('product_id').ids
        sales_history = request.env['sale.history'].sudo().search(
            ['|', ('active', '=', False), ('active', '=', True), ('partner_id', '=', main_partner),
              ('product_id', '!=', False),('product_id.categ_id.is_storage_contract','=',False)],limit=15,offset=0)
        # addons product filtering
        addons_products = sales_history.mapped('product_id').filtered(lambda rec: rec.need_sub_product).mapped('product_addons_list')
        if addons_products:
            sales_history = sales_history.filtered(lambda rec: rec.product_id not in addons_products)

        search_products = sales_history.mapped('product_id').ids
        context = {
            'default_sale_history_ids': [(6, 0, sales_history.ids)],
            'products': search_products
        }  
        values.update({
            'page_name': 'order_sheet_locations',
            'partner_id':partner_id,
            'order_sheet':"New",
            'sheet':sheet_id,
            'sale_history':sales_history,
            'total':len(sales_history),
            'offset':0

        })
       

        return request.render('website_order_sheet.user_sheet',values)


