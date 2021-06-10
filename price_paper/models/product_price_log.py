# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ProductPriceLog(models.Model):
    _name = 'product.price.log'
    _description = 'Product Price Log'

    product_id = fields.Many2one('product.product', string='Product')
    change_date = fields.Datetime(string='Date')
    old_price = fields.Float(string='Old Price', digits=dp.get_precision('Product Price'))
    new_price = fields.Float(string='New Price', digits=dp.get_precision('Product Price'))
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    partner_ids = fields.Many2many('res.partner', string='Partner')
    price_from = fields.Selection(string='From',
                            selection=[('sale', 'Sale Order'),
                                       ('manual', 'Manual'),
                                       ('standard', 'Standard Price Cron'),
                                       ('cost_cron', 'Cost Change Cron'),
                                       ('global_price', 'Global Price Change'),
                                       ('purchase', 'Purchase Order')])
    uom_id = fields.Many2one('uom.uom', string='UOM')
    type = fields.Selection(string='Type',
                            selection=[('cost', 'Cost'),
                                       ('burden', 'Burden Percentage'),
                                       ('std_price', 'Standard Price'),
                                       ('pricelist_price', 'Pricelist Price'),
                                       ('vendor_price', 'Vendor Price')])
    user_id = fields.Many2one('res.users', string='User')
    min_qty = fields.Float(string='Min Qty')
    trace_log = fields.Text(String='Log')

    @api.model
    def create(self, vals):
        try:
            import traceback
            trace = traceback.format_stack()
            log = "\nUser\t%s\n Records\t %s\n Time\t %s\n vals = %s\n\nlog=%s\n\n\n" % (self.env.user.name,self.ids,fields.Datetime.now(),vals,str(trace))
            if log:
                vals['trace_log'] = log
        except:
            pass
        return super(ProductPriceLog, self).create(vals)


ProductPriceLog()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
