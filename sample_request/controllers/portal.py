# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request


class PortalRequest(CustomerPortal):


    def _get_request_domain(self):
        cur_com = request.session.get('current_website_company',False)
        partner = request.env['res.partner'].browse([int(cur_com)]) if cur_com else request.env.user.partner_id
        return [('partner_id', '=', partner.id),('state','!=','draft')]


    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'request_count' in counters:
            request_count = request.env['sample.request'].search_count(self._get_request_domain()) \
                if request.env['sample.request'].check_access_rights('read', raise_exception=False) else 0
            values['request_count'] = request_count
        return values


    @http.route(['/my/requests', '/my/requests/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_requests(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        SampleRequest = request.env['sample.request']

        domain = self._get_request_domain()

        searchbar_sortings = {
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'state'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All Requests'), 'domain': []},
            'Approved': {'label': _('Approved Requests'), 'domain': [('state', '=', "approve")]},
            'Rejected': {'label': _('Rejected Requests'), 'domain': [('state', '=',"reject" )]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        request_count = SampleRequest.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/requests",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=request_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        requests = SampleRequest.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_requests_history'] = requests.ids[:100]

        values.update({
            'date': date_begin,
            'requests': requests,
            'page_name': 'request',
            'pager': pager,
            'default_url': '/my/requests',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby':filterby,
        })
        return request.render("sample_request.portal_my_requests", values)


    @http.route(['/my/request/<int:request_id>'], type='http', auth="public", website=True)
    def portal_request_page(self, request_id, access_token=None, message=False, download=False, **kw):
        try:
            sample_request_id = self._document_check_access('sample.request', request_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')


        values = {
            'sample_request': sample_request_id,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'page_name': 'request',
            'partner_id': sample_request_id.partner_id.id,
            'report_type': 'html',
            # 'action': sample_request_id._get_portal_return_action(),
        }
        # if sample_request_id.company_id:
        #     values['res_company'] = sample_request_id.company_id

        # Payment values
        # if sample_request_id.has_to_be_paid():
        #     logged_in = not request.env.user._is_public()

        #     acquirers_sudo = request.env['payment.acquirer'].sudo()._get_compatible_acquirers(
        #         sample_request_id.company_id.id,
        #         sample_request_id.partner_id.id,
        #         currency_id=sample_request_id.currency_id.id,
        #         sale_order_id=sample_request_id.id,
        #     )  # In sudo mode to read the fields of acquirers and partner (if not logged in)
        #     tokens = request.env['payment.token'].search([
        #         ('acquirer_id', 'in', acquirers_sudo.ids),
        #         ('partner_id', '=', sample_request_id.partner_id.id)
        #     ]) if logged_in else request.env['payment.token']

        #     # Make sure that the partner's company matches the order's company.
        #     if not payment_portal.PaymentPortal._can_partner_pay_in_company(
        #         sample_request_id.partner_id, sample_request_id.company_id
        #     ):
        #         acquirers_sudo = request.env['payment.acquirer'].sudo()
        #         tokens = request.env['payment.token']

        #     fees_by_acquirer = {
        #         acquirer: acquirer._compute_fees(
        #             sample_request_id.amount_total,
        #             sample_request_id.currency_id,
        #             sample_request_id.partner_id.country_id,
        #         ) for acquirer in acquirers_sudo.filtered('fees_active')
        #     }
        #     # Prevent public partner from saving payment methods but force it for logged in partners
        #     # buying subscription products
        #     show_tokenize_input = logged_in \
        #         and not request.env['payment.acquirer'].sudo()._is_tokenization_required(
        #             sale_order_id=sample_request_id.id
        #         )
        #     values.update({
        #         'acquirers': acquirers_sudo,
        #         'tokens': tokens,
        #         'fees_by_acquirer': fees_by_acquirer,
        #         'show_tokenize_input': show_tokenize_input,
        #         'amount': sample_request_id.amount_total,
        #         'currency': sample_request_id.pricelist_id.currency_id,
        #         'partner_id': sample_request_id.partner_id.id,
        #         'access_token': sample_request_id.access_token,
        #         'transaction_route': sample_request_id.get_portal_url(suffix='/transaction'),
        #         'landing_route': sample_request_id.get_portal_url(),
        #     })

        # if sample_request_id.state in ('draft', 'sent', 'cancel'):
        #     history = request.session.get('my_quotations_history', [])
        # else:
        #     history = request.session.get('my_orders_history', [])
        # values.update(get_records_pager(history, sample_request_id))

        return request.render('sample_request.sample_request_portal_template', values)

