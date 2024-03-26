# -*- coding: utf-8 -*-


from odoo.addons.website_sale.controllers.main import WebsiteSale
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.portal.controllers import portal
from odoo.osv.expression import AND, OR
from odoo.addons.portal.controllers.portal import pager as portal_pager

from odoo import http, _
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        curr_comapny = request.session.get('current_website_company')
        if not curr_comapny and not request.env.user._is_public():
            return request.redirect('/my/website/company')
        else:
            return super(WebsiteSale, self).product(product, category=category, search=search, **kwargs)

    def checkout_values(self, **kw):
        order = request.website.sale_get_order(force_create=True)
        shippings = []
        if order.partner_id != request.website.user_id.sudo().partner_id:
            Partner = order.partner_id.with_context(show_address=1).sudo()
            shippings = Partner.search([
                ("id", "child_of", order.partner_id.commercial_partner_id.ids),
                '|', ("type", "in", ["delivery", "other"]), ("id",
                                                             "=", order.partner_id.commercial_partner_id.id)
            ], order='id desc')

            curr_comapny = request.session['current_website_company']
            partner_com = request.env['res.partner'].sudo().browse(
                curr_comapny)
            access = request.env.user.partner_id.portal_contact_ids.mapped(
                'partner_id')
            # main_ship = partner_com.child_ids
            desired_shipping = shippings.filtered(
                lambda c: c.id in access.ids or c.id == partner_com.id)
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
            return super(CustomerPortal, self).home(**kw)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        ResPartner = request.env['res.partner']
        if 'manager_count' in counters:
            values['manager_count'] = ResPartner.search_count(self._prepare_manager_domain(partner)) \
                if ResPartner.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_manager_domain(self, partner):
        return [
            ('id', 'in', partner.child_ids.ids)
        ]

    def _get_manager_searchbar_sortings(self):
        return {
            'name': {'label': _('Name #'), 'order': 'name'},
        }

    def _get_searchbar_inputs_hirq(self):
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'name': {'input': 'name', 'label': _('Search in Name')},
            'email': {'input': 'email', 'label': _('Search in Email')},


        }

    def _get_search_domain_manager(self, search_in, search):
        search_domain = []
        if search_in in ('name', 'all'):
            search_domain = OR([search_domain, [('name', 'ilike', search)]])
        if search_in in ('email', 'all'):
            search_domain = OR(
                [search_domain, [('email', 'ilike', search)]])

        return search_domain

    def _prepare_managers_portal_rendering_values(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kwargs):
        ResPartner = request.env['res.partner']
        searchbar_sortings = self._get_manager_searchbar_sortings()
        searchbar_inputs = self._get_searchbar_inputs_hirq()

        if not sortby:
            sortby = 'name'
        values = self._prepare_portal_layout_values()
        url = "/my/managers"
        domain = self._prepare_manager_domain(request.env.user.partner_id)
        sort_order = searchbar_sortings[sortby]['order']

        if search and search_in:
            domain += self._get_search_domain_manager(search_in, search)

        if not filterby:
            filterby = 'all'

        pager_values = portal_pager(
            url=url,
            total=ResPartner.search_count(domain),
            page=page,
            step=self._items_per_page,
            url_args={
                'sortby': sortby, 'search_in': search_in,
                'search': search,
                'filterby': filterby,
                'groupby': groupby},
        )
        res_partner = ResPartner.search(
            domain, order=sort_order, limit=self._items_per_page, offset=pager_values['offset'])

        values.update({
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
            'ResPartners': res_partner.sudo(),
            'page_name': 'my_managers',
            'pager': pager_values,
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return values

    @http.route(['/my/managers', '/my/managers/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_managers(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kwargs):
        values = self._prepare_managers_portal_rendering_values(
            page=page, sortby=sortby, filterby=filterby, search=search, search_in=search_in, groupby=groupby, **kwargs)
        return request.render("portal_enhancements.portal_my_managers", values)

    @http.route(['/my/manager/edit/<int:partner_id>'],type='http',auth='user',website=True)        
    def edit_manager(self,partner_id):
        partner_id = request.env["res.partner"].browse([int(partner_id)])
        partner_id_main = request.env.user.partner_id
        manage_managers = True if partner_id_main.portal_access_level == 'user' else False
        if not manage_managers:
            raise Forbidden()
        allowed_compaines = partner_id_main.portal_company_ids
        partner_allowed = partner_id.portal_company_ids.ids
        partner_portal_model_access = partner_id.portal_model_access.mapped("model_id").ids
        values = {'allowed_compaines': allowed_compaines,'manage_access': partner_id_main.portal_model_access, 'page_name': 'my_managers_edit','partner_id':partner_id,'partner_allowed':partner_allowed,'partner_portal_model_access':partner_portal_model_access}
        return request.render('portal_enhancements.edit_manager', values)


    @http.route(['/my/manager/new'], type='http', auth="user", website=True)
    def create_new_manager(self):
        partner_id = request.env.user.partner_id
        manage_managers = True if partner_id.portal_access_level == 'user' else False
        if not manage_managers:
            raise Forbidden()

        allowed_compaines = partner_id.portal_company_ids

        values = {'allowed_compaines': allowed_compaines,
                  'manage_access': partner_id.portal_model_access, 'page_name': 'my_managers_new'}
        return request.render('portal_enhancements.new_manager', values)

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id
        sale_access = partner_id._check_portal_model_access('sale.order')
        invoice_access = partner_id._check_portal_model_access('account.move')
        purchase_access = partner_id._check_portal_model_access(
            'purchase.order')
        lead_access = partner_id._check_portal_model_access('crm.lead')
        calendar_access = partner_id._check_portal_model_access(
            'calendar.event')
        ticket_access = partner_id._check_portal_model_access(
            'helpdesk.ticket')
        project_access = partner_id._check_portal_model_access(
            'project.project')
        sign_access = partner_id._check_portal_model_access(
            'sign.request.item')
        timesheet_access = partner_id._check_portal_model_access(
            'account.analytic.line')
        manage_managers = True if partner_id.portal_access_level == 'user' else False

        values.update(
            sale_access=sale_access,
            invoice_access=invoice_access,
            purchase_access=purchase_access,
            lead_access=lead_access,
            calendar_access=calendar_access,
            ticket_access=ticket_access,
            project_access=project_access,
            sign_access=sign_access,
            timesheet_access=timesheet_access,
            manage_managers=manage_managers
        )

        return values

    @http.route()
    def home(self, **kw):
        if not request.session.get('current_website_company'):
            return request.redirect('/my/website/company')
        else:
            return super(CustomerPortal, self).home(**kw)

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
        if request.env.user.has_group('base.group_user'):
            portal_companies = request.env['res.partner'].sudo().search([('is_company','=',True)])
        if (company_id and int(company_id) in portal_companies.ids):
            request.session['current_website_company'] = int(company_id)
            orders = request.env['sale.order'].search_count(
                [('partner_id', '=', int(company_id)), ('state', '=', 'draft')])
            website = request.env['website'].sudo().search([])
            print(website)
            order = website.sale_get_order(website=website, force_create=False)

            if order.partner_id.id != int(company_id):
                website.sale_reset()
            if orders:
                return {'status': True, 'url': '/select/cart'}
            return {'status': True}
        else:
            request.session['current_website_company'] = None
            return {'status': False}

    @http.route(['/select/cart'], type='http', auth='user', website=True, csrf=False)
    def delivery_cart(self, **kw):
        curr_comapny = request.session.get('current_website_company')
        orders = request.env['sale.order'].sudo().search(
            [('partner_id', '=', int(curr_comapny)), ('state', '=', 'draft')])
        if not orders:
            return request.redirect('/shop')
        else:
            return request.render('portal_enhancements.multiple_cart', {'sale_order_ids': orders})

    @http.route('/set/cart/order/<int:order_id>', type='http', auth='user', website=True, csrf=False)
    def set_cart_order(self, order_id):
        order = request.env['sale.order'].browse([int(order_id)])
        request.website.sale_reset()
        request.session.update({
            'sale_order_id': order.sudo().id,
            'website_sale_current_pl': order.sudo().pricelist_id.id,
            'sale_last_order_id': order.id
        })
        return request.redirect('/shop/cart')

    @http.route(['/my/website/company'], type='http', auth="user", website=True)
    def portal_company_switch(self):
        partner = request.env.user.partner_id
        portal_companies = partner.portal_company_ids
        if request.env.user.has_group('base.group_user'):
            portal_companies = request.env['res.partner'].sudo().search([('is_company','=',True)])
        curr_comapny = request.session.get('current_website_company')

        return request.render("portal_enhancements.portal_my_company", {'company_ids': portal_companies, 'curr_comapny': curr_comapny})




    @http.route('/my/manager/create', type='json', auth='user', website=True)
    def create_manager(self, name, email, phone, note, model_access, comany_access,partner_id = False):
        if not partner_id:
            partner_id = request.env.user.partner_id

            child_partner_id = request.env['res.partner'].sudo().create({
                'parent_id': partner_id.id,
                'name': name,
                'email': email,
                'phone': phone,
                'comment': note,
                'portal_access_level': 'manager',
                'portal_company_ids': [(6, 0, list(map(int, comany_access)))],
                'portal_model_access': [(0, 0, {'model_id': int(rec), 'is_model_accessible': True}) for rec in model_access]
            })
            print(child_partner_id)

            helpdesk_vals = {
                'name':f'New Manager: "{name}" Approval',
                'partner_id':partner_id.id
            }
            Website = request.env['website']
            curr_web = Website.get_current_website()
            team_id = curr_web.helpdesk_team_website.id
            if team_id:
                helpdesk_vals['team_id'] = team_id.id
            ticket_id = request.env['helpdesk.ticket'].sudo().create(helpdesk_vals)
        
            acttion = request.env.ref('portal_enhancements.action_res_partner_portal_enhancements')

            ticket_id.message_post(body=("New Manager Have been created kindly approve and grant Access") + " <a href='/web#id=%s&action=%s&model=res.partner&view_type=form' data-oe-model=res.partner>%s</a>" % (child_partner_id.id,acttion.id,child_partner_id.name))
        else:
            partner = request.env['res.partner'].sudo().browse([int(partner_id)])
            partner.portal_model_access.unlink()
            partner.write({
                'name': name,
                'email': email,
                'phone': phone,
                'comment': note,
                'portal_access_level': 'manager',
                'portal_company_ids': [(6, 0, list(map(int, comany_access)))],
                'portal_model_access': [(0, 0, {'model_id': int(rec), 'is_model_accessible': True}) for rec in model_access]
            })
        return {
                'status':True
            }
