# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    check_bounce_product = fields.Many2one('product.product', string='Check Bounce Product')
    check_bounce_term = fields.Many2one('account.payment.term', string='Check Bounce Payment Term')


ResCompany()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
