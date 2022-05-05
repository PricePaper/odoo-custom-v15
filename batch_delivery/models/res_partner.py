# -*- coding: utf-8 -*-

from werkzeug.urls import Href
from odoo import models, fields, api, _
from odoo.exceptions import UserError


def urlplus(url, params):
    return Href(url)(params or None)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_driver = fields.Boolean(string='Truck Driver')
    delivery_notes = fields.Text(string='Delivery Notes')
    bill_with_goods = fields.Boolean(string='Bill With Goods', default=True)
    location_url = fields.Char(compute='compute_location_url', string="Location URL")
    is_driver_available = fields.Boolean(string='Is Driver Available', default=True)
    private_partner = fields.Boolean(string='Is Private', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        if self._context.get('search_default_customer') and vals_list:
                vals_list[0]['customer'] = True
        return super(ResPartner, self).create(vals_list)

    @api.depends('partner_latitude', 'partner_longitude')
    def compute_location_url(self):
        """
        Compute the location url from partner latitude and longitude
        """
        for rec in self:
            rec.location_url = False
            if rec.partner_latitude and rec.partner_longitude:
                params = {'partner_ids': rec.id,
                          'partner_url': rec.customer and 'customers' or 'partners'
                          }
                rec.location_url = urlplus('/google_map', params)

    def view_partner_location(self):
        """
        Method to view the location in google map.
        """
        if not self.location_url:
            raise UserError("Map not available, check latitude and longitude")
        return {
            'name': 'Partner Location',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': self.location_url or ""
        }

    # Todo don't know the usage'
    # def open_action_followup(self):
    #     return {}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
