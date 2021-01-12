# -*- coding: utf-8 -*-

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
from odoo.addons.price_paper.models import margin
from odoo.tools import float_round


class ProductStandardPrice(models.Model):
    _name = "product.standard.price"
    _description = 'Product Standard Price'

    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    price = fields.Float(string="Standard Price")
    cost = fields.Float(string="cost", compute='compute_cost', store=False)
    price_margin = fields.Float(string='Margin %', compute='compute_margin', digits=dp.get_precision("Product Price"))

    @api.depends('price', 'product_id.cost', 'cost')
    def compute_margin(self):
        for rec in self:
            if rec.cost:
                rec.price_margin = margin.get_margin(rec.price, rec.cost, percent=True)

    @api.depends('product_id.cost', 'uom_id')
    def compute_cost(self):
        for rec in self:
            if rec.product_id and rec.product_id.cost:
                if rec.uom_id != rec.product_id.uom_id:
                    cost = rec.product_id.uom_id._compute_price(rec.product_id.cost, rec.uom_id)
                    rec.cost = float_round(cost * (1 + (rec.product_id.categ_id.repacking_upcharge / 100)),
                                           precision_digits=2)
                else:
                    rec.cost = rec.product_id.cost
            else:
                rec.cost = 0

    @api.multi
    def write(self, vals):
        """
        product price log
        """

        if 'price' in vals:
            price = float_round(vals.get('price'), precision_digits=2)
            log_vals = {'change_date': fields.Datetime.now(),
                        'type': 'std_price',
                        'old_price': self.price,
                        'new_price': price,
                        'user_id': self.env.user.id,
                        'price_from': 'manual',
                        'uom_id': self.uom_id.id,
                        'product_id': self.product_id.id
                        }
            if self._context.get('user', False):
                log_vals['user_id'] = self._context.get('user', False)
            if self._context.get('from_standardprice_cron', False):
                log_vals['price_from'] = 'standard'
            if self._context.get('cost_cron', False):
                log_vals['price_from'] = 'cost_cron'
            self.env['product.price.log'].create(log_vals)
        result = super(ProductStandardPrice, self).write(vals)
        return result

    @api.model
    def create(self, vals):
        res = super(ProductStandardPrice, self).create(vals)
        if 'price' in vals:
            log_vals = {'change_date': fields.Datetime.now(),
                        'type': 'std_price',
                        'new_price': vals.get('price'),
                        'user_id': self.env.user.id,
                        'price_from': 'manual',
                        'uom_id': res.uom_id.id,
                        'product_id': res.product_id.id
                        }
            if self._context.get('user', False):
                log_vals['user_id'] = self._context.get('user', False)
            if self._context.get('from_standardprice_cron', False):
                log_vals['price_from'] = 'standard'
            self.env['product.price.log'].create(log_vals)
        return res


ProductStandardPrice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
