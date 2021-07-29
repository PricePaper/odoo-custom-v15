# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductNotes(models.Model):
    _name = 'product.notes'
    _description = 'Product Notes'

    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Customer')
    notes = fields.Text(string='Notes')
    expiry_date = fields.Date('Valid Upto')


ProductNotes()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
