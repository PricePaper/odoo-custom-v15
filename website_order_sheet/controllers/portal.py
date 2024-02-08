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
            sheet_count = len(request.env.user.partner_id.delivery_location)
            values['sheet_count'] = sheet_count
        return values
    
    @http.route(['/my/order/sheet', '/my/order/sheet/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_requests_test(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        delivery_location = request.env.user.partner_id.delivery_location
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
        
        # products = self.order_line.mapped('product_id').ids
        sales_history = request.env['sale.history'].sudo().search(
            ['|', ('active', '=', False), ('active', '=', True), ('partner_id', '=', partner_id),
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


