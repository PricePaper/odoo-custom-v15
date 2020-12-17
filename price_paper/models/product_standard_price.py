# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.addons.price_paper.models import margin
import odoo.addons.decimal_precision as dp
from odoo.tools import float_round

class ProductStandardPrice(models.Model):
    _name = "product.standard.price"

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
                    rec.cost = float_round(cost * (1+(rec.product_id.categ_id.repacking_upcharge/100)), precision_digits=2)
                else:
                    rec.cost = rec.product_id.cost
            else:
                rec.cost = 0



ProductStandardPrice()
