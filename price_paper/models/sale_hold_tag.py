# -*- coding: utf-8 -*-

from odoo import fields, models


class PartnerCategory(models.Model):
    _description = 'Sale Hold Tags'
    _name = 'sale.hold.tag'
    _order = 'name'

    name = fields.Char(string='Tag Name')
    sale_ids = fields.Many2many('sale.order', column1='hold_tag_id', column2='sale_id', string='Sale Orders', copy=False)
    code = fields.Char(string='Code')
