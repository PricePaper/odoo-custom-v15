# -*- coding: utf-8 -*-


from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo.addons.portal.controllers import portal

from odoo import http, _
from odoo.http import request



class WebsiteSale(WebsiteSale):
    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        curr_comapny = request.session.get('current_website_company')
        if not curr_comapny and not request.env.user._is_public():
            return request.redirect('/my/website/company')
        else:
            return super(WebsiteSale,self).product(product, category=category, search=search, **kwargs)

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



class CustomerPortal(portal.CustomerPortal):
    @http.route()
    def home(self, **kw):
        if not request.session.get('current_website_company'):
            return request.redirect('/my/website/company')
        else:
            return super(CustomerPortal,self).home(**kw)
       


    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id
        sale_access = partner_id._check_portal_model_access('sale.order')
      
        values['sale_access'] = sale_access 

        return values


    @http.route()
    def home(self, **kw):
        if not request.session.get('current_website_company'):
            return request.redirect('/my/website/company')
        else:
            return super(CustomerPortal,self).home(**kw)
       


    def _prepare_quotations_domain(self, partner):
        curr_comapny = request.session.get('current_website_company')

        partner_com = False
        if curr_comapny:
            partner_com = request.env['res.partner'].sudo().browse(
                curr_comapny)

        exising_shipping = partner.portal_contact_ids.partner_id.ids
        desired_shipping = partner_com.child_ids.filtered(
            lambda c: c.type == 'delivery' and c.id in exising_shipping).ids
        if desired_shipping and partner_com.child_ids:
            desired_shipping.append((curr_comapny))
        else:
            desired_shipping = [curr_comapny]

        return [
            ('partner_id', '=', curr_comapny),
            ('partner_shipping_id', 'in', desired_shipping),
            ('state', 'in', ['sent', 'cancel'])
        ]

    def _prepare_orders_domain(self, partner):
        # overridden to modify domain
        curr_comapny = request.session.get('current_website_company')

        partner_com = False
        if curr_comapny:
            partner_com = request.env['res.partner'].sudo().browse(
                curr_comapny)

        exising_shipping = partner.portal_contact_ids.partner_id.ids
        desired_shipping = partner_com.child_ids.filtered(
            lambda c: c.type == 'delivery' and c.id in exising_shipping).ids
        if desired_shipping and partner_com.child_ids:
            desired_shipping.append((curr_comapny))
        else:
            desired_shipping = [curr_comapny]

        return [
            ('partner_id', '=', curr_comapny),
            ('partner_shipping_id', 'in', desired_shipping),
            ('state', 'in', ['sale', 'done'])
        ]

    @http.route('/set/company', type='json', auth='user', websiste=True)
    def set_company(self, company_id):
        partner = request.env.user.partner_id
        portal_companies = partner.portal_company_ids
        if (company_id and int(company_id) in portal_companies.ids):
            request.session['current_website_company'] = int(company_id)
            orders = request.env['sale.order'].search_count([('partner_id','=',int(company_id)),('state','=','draft')])
            website = request.env['website'].sudo().search([])
            print(website)
            order = website.sale_get_order(website=website,force_create=False)
            
            if order.partner_id.id != int(company_id):
                website.sale_reset()
            if orders:
                return {'status':True,'url':'/select/cart'}
            return {'status': True}
        else:
            request.session['current_website_company'] = None
            return {'status': False}


    @http.route(['/select/cart'],type='http',auth='user',website=True,csrf=False)
    def delivery_cart(self,**kw):
        curr_comapny = request.session.get('current_website_company')
        orders = request.env['sale.order'].search([('partner_id','=',int(curr_comapny)),('state','=','draft')])
        if not orders:
            return request.redirect('/shop')
        else:
            return request.render('portal_enhancements.multiple_cart',{'sale_order_ids':orders})

    @http.route('/set/cart/order/<int:order_id>',type='http',auth='user',website=True,csrf=False)
    def set_cart_order(self,order_id):
        order = request.env['sale.order'].browse([int(order_id)])
        request.website.sale_reset()
        request.session.update({
            'sale_order_id': order.sudo().id,
            'website_sale_current_pl': order.sudo().pricelist_id.id,
            'sale_last_order_id' : order.id
        })
        return request.redirect('/shop/cart')

    @http.route(['/my/website/company'], type='http', auth="user", website=True)
    def portal_company_switch(self):
        partner = request.env.user.partner_id
        portal_companies = partner.portal_company_ids
        curr_comapny = request.session.get('current_website_company')

        return request.render("portal_enhancements.portal_my_company", {'company_ids': portal_companies,'curr_comapny':curr_comapny})
