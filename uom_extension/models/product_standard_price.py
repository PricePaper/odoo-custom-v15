# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.price_paper.models import margin
from odoo.tools import float_round


class ProductStandardPrice(models.Model):
    _inherit = 'product.standard.price'

    @api.depends('product_id.cost', 'uom_id', 'product_id.ppt_uom_id')
    def compute_cost(self):
        for rec in self:
            if rec.product_id and rec.product_id.cost and rec.product_id.ppt_uom_id:
                if rec.uom_id != rec.product_id.ppt_uom_id:
                    cost = rec.product_id.ppt_uom_id._compute_price(rec.product_id.cost, rec.uom_id)
                    rec.cost = float_round(cost * (1 + (rec.product_id.categ_id.repacking_upcharge / 100)),
                                           precision_digits=2)
                else:
                    rec.cost = rec.product_id.cost
            else:
                rec.cost = 0
