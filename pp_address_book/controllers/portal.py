# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo import tools,_
import logging
_logger = logging.getLogger(__name__)

class PortalRequest(CustomerPortal):

    @http.route(['/my/address/book'], type='http', auth="user", website=True)
    def portal_my_addresss(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id
        child_ids = partner_id.child_ids
        contact = child_ids.filtered(lambda x: x.type=='contact')
        inv_add = child_ids.filtered(lambda x: x.type=='invoice')
        del_add = child_ids.filtered(lambda x: x.type=='delivery')
        values.update(contact=contact,inv_add=inv_add,del_add=del_add,child_ids = child_ids,page_name='address_book')
        return request.render("pp_address_book.portal_my_address", values)
    



    def render_address(self, partner_id, error={}):
        params = {
            "partner_id": partner_id,
            "countries": request.env['res.country'].get_website_sale_countries(),
            "country": partner_id.country_id if partner_id else '',
            "error": error,
            "page_name":'address_book',
            "child_address":True
        }

        response = request.render('pp_address_book.address_book', params)
        return response

    def _get_mandatory_address_fields(self):
        return ["name", "email", "street","city","country_id"]

    def address_form_validate(self, data):
        error = dict()
        error_message = []

        required_fields = self._get_mandatory_address_fields()
        country = request.env['res.country']
        if data.get('country_id'):
            country = country.browse(int(data.get('country_id')))
            if 'state_code' in country.get_address_fields() and country.state_ids:
                required_fields += ['state_id']

        for field_name in required_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(
                _('Invalid Email! Please enter a valid email address.'))

        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        return error, error_message


    
    @http.route(['/portal/grant/access'],type='json',auth="user",website=True)
    def grant_portal_access(self,partner_id,portal=True):
        result ={}
        try:
            portal_wizard = request.env['portal.wizard'].sudo().create({
                'partner_ids':[(6,0,[int(partner_id)])]
            })
            if portal:
                portal_wizard.user_ids.action_grant_access()
            else:
                portal_wizard.user_ids.action_revoke_access()
        except Exception as e:
            result['error']=e
        return result
    
    @http.route(['/delete/address'],type='json',auth="user",website=True)
    def delete_address(self,partner_id,**kw):
        acutal_partner_id = request.env.user.partner_id.sudo()
        partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
        if acutal_partner_id == partner_id:
            return {
                "status":False,
                "message":_('YOU CANNOT EDIT PRIMARY ADDRESS')
            }
        else:
            try:
                partner_id.toggle_active()
            except Exception as e:
                _log.info("=ERROR ON DELETING ADDRESS {}".format(e))
            return {
                "status": True,
            }
        

    @http.route(['/my/address/<int:partner_id>', '/my/address'], type='http', auth="user", website=True, methods=['GET', 'POST'])
    def user_address(self, partner_id=None, **kw):
        acutal_partner_id = request.env.user.partner_id.sudo()
        Partner = request.env['res.partner'].with_context(
            show_address=1).sudo()
        if partner_id:
            partner_id = Partner.browse(int(partner_id))
            if acutal_partner_id == partner_id:
                error = {'error_message':[_('YOU CANNOT EDIT PRIMARY ADDRESS')]}
                return self.render_address(partner_id,error)

        if request.httprequest.method == 'GET':
            partner = partner_id if partner_id else False
            return self.render_address(partner)

        if request.httprequest.method == 'POST':
            error, error_message = self.address_form_validate(kw)
            if error:
                error['error_message'] = error_message
                partner_id=partner_id if partner_id else False
                return self.render_address(partner_id, error)
            else:
                if not kw.get('state_id'):
                    partner_id.state_id = None
                else:
                    kw['state_id'] = int(kw['state_id'])
                kw['country_id'] = int(kw['country_id'])
                if not partner_id:
                    partner_id = request.env['res.partner'].sudo().with_context(default_parent_id=acutal_partner_id.id).create([kw])
                else:
                    partner_id.write(kw)

                

        return request.redirect("/my/address/book")