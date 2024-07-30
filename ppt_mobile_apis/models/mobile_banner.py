# -*- coding: utf-8 -*-

from odoo import api, models, fields
import json


class MobileBanner(models.Model):
    _name = 'mobile.banner'


    banner = fields.Binary(string='Banner',required=True)
    url = fields.Char(string='Url',required=True)
    complete_url = fields.Char('complete_url',compute='_get_url',store=True)

    
    @api.depends('url')
    def _get_url(self):
        for rec in self:
            # self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if rec.url and  rec.url.startswith('/'):
                rec.complete_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + rec.url
            else:
                rec.complete_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') +'/'+ str(rec.url)
