# -*- coding: utf-8 -*-

from odoo.addons.portal.controllers import portal
from odoo import http, _
from odoo.http import request


class CustomerPortal(portal.CustomerPortal):
    @http.route()
    def home(self, **kw):
        if not request.session['current_website_company']:
            return request.redirect('/my/website/company')
        else:
            return super(CustomerPortal,self).home(**kw)
       


    def _prepare_quotations_domain(self, partner):
        curr_comapny = request.session['current_website_company']

        partner_com = False
        if curr_comapny:
            partner_com = request.env['res.partner'].sudo().browse(
                curr_comapny)

        exising_shipping = partner.portal_contact_ids.partner_id.ids
        desired_shipping = [partner_com.child_ids.filtered(
            lambda c: c.type == 'delivery' and c.id in exising_shipping)]
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
        curr_comapny = request.session['current_website_company']

        partner_com = False
        if curr_comapny:
            partner_com = request.env['res.partner'].sudo().browse(
                curr_comapny)

        exising_shipping = partner.portal_contact_ids.partner_id.ids
        desired_shipping = [partner_com.child_ids.filtered(
            lambda c: c.type == 'delivery' and c.id in exising_shipping)]
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
            return {'status': True}
        else:
            request.session['current_website_company'] = None
            return {'status': False}

    @http.route(['/my/website/company'], type='http', auth="user", website=True)
    def portal_company_switch(self):
        partner = request.env.user.partner_id
        portal_companies = partner.portal_company_ids
        return request.render("portal_enhancements.portal_my_company", {'company_ids': portal_companies})
