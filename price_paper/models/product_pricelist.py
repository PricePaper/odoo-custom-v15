# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime,date
from dateutil.relativedelta import relativedelta


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'


    type = fields.Selection(string='Type', selection=[('customer', 'Customer'), ('shared', 'Shared'), ('competitor', 'Competitor')])
    customer_pricelist_ids = fields.One2many('customer.pricelist', 'pricelist_id')
    customer_product_price_ids = fields.One2many('customer.product.price', 'pricelist_id')
    expiry_date = fields.Date('Valid Upto')
    price_lock = fields.Boolean(string='Price Change Lock', default=False)
    lock_expiry_date = fields.Date(string='Lock Expiry date')
    customer_ids = fields.Many2many('res.partner', string='Customers',compute='_compute_partner', store=False)

    @api.onchange('price_lock')
    def onchange_price_lock(self):
        if self.price_lock:
            if self.env.user.company_id and self.env.user.company_id.price_lock_days:
                days = self.env.user.company_id.price_lock_days
                self.lock_expiry_date =  date.today()+relativedelta(days=days)
        else:
            self.lock_expiry_date = False

    @api.depends('customer_pricelist_ids')
    def _compute_partner(self):
        for pricelist in self:
            if pricelist.type != 'competitor':
                partner_ids = pricelist.customer_pricelist_ids.mapped('partner_id').ids
                if partner_ids:
                    pricelist.customer_ids = [(6, 0, partner_ids)]


    @api.model
    def _cron_update_price_change_lock(self):
        domain = [('price_lock', '=', True), ('lock_expiry_date', '<', datetime.today())]
        pricelists = self.search(domain)
        product_prices = self.env['customer.product.price'].search(domain)
        vals = {
            'price_lock': False,
            'lock_expiry_date': False
        }
        pricelists.write(vals)
        product_prices.write(vals)


ProductPricelist()
