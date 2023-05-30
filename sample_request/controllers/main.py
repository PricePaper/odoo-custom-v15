from odoo.addons.website_sale.controllers import main
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.fields import Command
from odoo.http import request
from werkzeug.exceptions import Forbidden, NotFound
import logging 
_logger = logging.getLogger(__name__)

class WebsiteSale(main.WebsiteSale):

    




    def checkout_request_redirection(self,request_id):
        if not request_id or request_id.state != 'draft':
            request.session['sample_request_id'] = None
            return request.redirect('/shop')

        if request_id and not request_id.request_lines:
            return request.redirect('/sample/request')


    def checkout_values_request(self, **kw):
        request_id = request.website.get_sample_oder(force_create=1)
        shippings = []
        if request_id.partner_id != request.website.user_id.sudo().partner_id:
            Partner = request_id.partner_id.with_context(show_address=1).sudo()
            shippings = Partner.search([
                ("id", "child_of", request_id.partner_id.commercial_partner_id.ids),
                '|', ("type", "in", ["delivery", "other"]), ("id", "=", request_id.partner_id.commercial_partner_id.id)
            ], order='id desc')
            

        values = {
            'request_id': request_id,
            'shippings': shippings,
        }
        return values
            

    @http.route(['/sample/request/update'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def sample_request(self, product_id, **kw):
        sample_request = request.website.get_sample_oder(force_create=1)
        result = sample_request._update_sample_order(product_id=product_id)
        return result


    @http.route(['/sample/request'], type='http', auth="public", website=True, csrf=False)
    def sample_request_cart(self):
        sample_order = request.website.get_sample_oder(force_create=False)
        return request.render('sample_request.request_cart',{'sample':sample_order})

    @http.route(['/sample/address'], type='http', auth="public", website=True, csrf=False)
    def sample_address(self):
        request_id = request.website.get_sample_oder()

        redirection = self.checkout_request_redirection(request_id)
        if redirection:
            return redirection

        values = self.checkout_values_request()

        return request.render("sample_request.request_checkout", values)

    @http.route(['/sample/confirm_order'], type='http', auth="public", website=True, csrf=False)
    def sample_confirm(self):
        request_id = request.website.get_sample_oder()
        redirection = self.checkout_request_redirection(request_id)
        if redirection:
            return redirection
        crm_vals ={
            'name':f'{request_id.partner_id.name} sample request.',
            'partner_id':request_id.partner_id.id,
            'sample_request_id':request_id.id
        }
        crm =  request.env['crm.lead'].sudo().create(crm_vals)
        request_id.lead_id = crm.id
        request_id.state='request'

        return request.render("sample_request.sample_request", {'request_id':request_id})


    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(product=product, category=category, search=search, **kwargs)
        res.qcontext['sample_access'] = True
        return res


    @http.route(['/sample/address/edit'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def sample_ddress(self, **kw):
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        sample_request = request.website.get_sample_oder(force_create=1)

        redirection = self.checkout_request_redirection(sample_request)

        if redirection:
            return redirection

        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if sample_request.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == sample_request.partner_id.id:
                    mode = ('edit', 'billing')
                    can_edit_vat = sample_request.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([('id', 'child_of', sample_request.partner_id.commercial_partner_id.ids)])
                    if sample_request.partner_id.commercial_partner_id.id == partner_id:
                        mode = ('new', 'shipping')
                        partner_id = -1
                    elif partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else: # no mode - refresh without post?
                return request.redirect('/sample/address')

        # IF POSTED
        if 'submitted' in kw and request.httprequest.method == "POST":
            pre_values = self.values_preprocess(sample_request, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(sample_request, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                # We need to validate _checkout_form_save return, because when partner_id not in shippings
                # it returns Forbidden() instead the partner_id
                if isinstance(partner_id, Forbidden):
                    return partner_id
                if mode[1] == 'billing':
                    sample_request.partner_id = partner_id
                    # sample_request.with_context(not_self_saleperson=True).onchange_partner_id()
                    # # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    # sample_request.partner_invoice_id = partner_id
                    # if not kw.get('use_same'):
                    #     kw['callback'] = kw.get('callback') or \
                    #         (not sample_request.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
                    # # We need to update the pricelist(by the one selected by the customer), because onchange_partner reset it
                    # We only need to update the pricelist when it is not redirected to /confirm_order
                    # if kw.get('callback', '') != '/shop/confirm_order':
                    #     request.website.sale_get_order(update_pricelist=True)
                elif mode[1] == 'shipping':
                    sample_request.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                # -> TDE: you are the guy that did what we should never do in commit e6f038a
                # sample_request.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect('/sample/address')

        render_values = {
            'sample_request': sample_request,
            'website_sale_order':sample_request,
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'error': errors,
            'callback': kw.get('callback'),
            # 'only_services': order and order.only_services,
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("sample_request.sample_address", render_values)






