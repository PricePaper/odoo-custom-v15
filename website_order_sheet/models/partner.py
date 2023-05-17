# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    delivery_location = fields.Many2many('res.partner','partner_del_location','partner_id','partner_dest_id',string='Delivery Locations')