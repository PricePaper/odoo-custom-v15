# -*- coding: utf-8 -*-

from odoo import fields, models


class CustomerPricelist(models.Model):
    _name = 'customer.pricelist'
    _description = 'Customer Pricelist Link'
    _rec_name = 'pricelist_id'

    sequence = fields.Integer(string='Sequence')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', ondelete='cascade', )
    partner_id = fields.Many2one('res.partner', string='Customer', ondelete='cascade', )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
