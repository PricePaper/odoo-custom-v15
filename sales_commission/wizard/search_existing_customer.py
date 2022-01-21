# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SearchExistingCustomer(models.TransientModel):
    _name = "search.existing.customer"
    _description = 'Search Existing Customer'

    search_string = fields.Char(string='Search',
                                help='Search... Name,email,phone,city,mobile,vat,city')
    line_ids = fields.One2many('existing.customer.line', 'parent_id', string='Result')




class ExistingCustomerLine(models.TransientModel):
    _name = "existing.customer.line"
    _description = 'Existing Customer Line'

    name = fields.Char(string='Customer Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    tin = fields.Char(string='Tin')
    last_so = fields.Char(string='Last Sale order')
    last_so_date = fields.Date(string='Last Sale Date')
    parent_id = fields.Many2one('search.existing.customer', string='Parent')
    # parent_partner = fields.Many2one('res.partner', string='Parent')
    city = fields.Char(string='City')
    sales_person = fields.Char(string='Salesperson')




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
