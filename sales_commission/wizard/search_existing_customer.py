# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SearchExistingCustomer(models.TransientModel):
    _name = "search.existing.customer"
    _description = 'Search Existing Customer'

    search_string = fields.Char(string='Search',
                                help='Search... Name,email,phone,city,mobile,vat,city')
    line_ids = fields.One2many('existing.customer.line', 'parent_id', string='Result')

    @api.onchange('search_string')
    def search_existing_customer(self):
        self.line_ids = False
        if self.search_string:
            string_val = self.search_string.replace("'", "''")
            string = '%' + string_val + '%'
            query = """SELECT name, commercial_company_name, email, phone, mobile, vat, last_so, last_sold_date, city, id from res_partner where (name ilike('%s') or phone ilike('%s') or mobile ilike('%s') or email ilike('%s') or commercial_company_name ilike('%s') or vat ilike('%s') or city ilike('%s')) and customer=True and parent_id IS NULL and is_sales_person=False;""" % (
            string, string, string, string, string, string, string)
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            if result:
                res = []
                for rec in result:
                    salepersons = self.env['res.partner'].sudo().browse(rec[9]).mapped('sales_person_ids')
                    salreps = ''
                    salreps = ','.join(saleperson.name for saleperson in salepersons)
                    val = {'name': rec[0],
                           'email': rec[2],
                           'phone': rec[3],
                           'mobile': rec[4],
                           'tin': rec[5],
                           'last_so': rec[6],
                           'last_so_date': rec[7],
                           'parent_id': self.id,
                           'city': rec[8],
                           'sales_person': salreps
                           }
                    res.append((0, _, val))
                self.line_ids = res
            else:
                self.line_ids = False
        else:
            self.line_ids = False


SearchExistingCustomer()


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


ExistingCustomerLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
