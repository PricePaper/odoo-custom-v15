# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round

class ChangeProductUom(models.Model):
    _inherit = 'cost.change'

    def calculate_new_price(self, pricelist=None):

        if not pricelist:
            return 0
        new_price = 0
        product = pricelist.product_id
        old_working_cost = product.cost
        old_list_price = pricelist.price
        if product.ppt_uom_id != pricelist.product_uom:
            old_working_cost = product.ppt_uom_id._compute_price(product.cost, pricelist.product_uom) * (
                    (100 + product.categ_id.repacking_upcharge) / 100)

        if old_list_price:
            margin = (old_list_price - old_working_cost) / old_list_price

            if self.price_filter == 'fixed':
                new_working_cost = self.price_change * ((100 + product.burden_percent) / 100)
                if self.cost_change_parent.update_burden and self.burden_change:
                    new_working_cost = self.price_change * ((100 + self.burden_change) / 100)
                if product.ppt_uom_id != pricelist.product_uom:
                    new_price = (product.ppt_uom_id._compute_price(new_working_cost, pricelist.product_uom) * (
                            (100 + product.categ_id.repacking_upcharge) / 100)) / (1 - margin)
                else:
                    new_price = new_working_cost / (1 - margin)
            else:
                new_working_cost = (product.standard_price * (100 + self.price_change) / 100) * (
                        (100 + product.burden_percent) / 100)
                if self.cost_change_parent.update_burden and self.burden_change:
                    new_working_cost = (product.standard_price * (100 + self.price_change) / 100) * (
                            (100 + self.burden_change) / 100)
                if product.ppt_uom_id != pricelist.product_uom:
                    new_price = (product.ppt_uom_id._compute_price(new_working_cost, pricelist.product_uom) * (
                            (100 + product.categ_id.repacking_upcharge) / 100)) / (1 - margin)
                else:
                    new_price = new_working_cost / (1 - margin)
        return new_price

    def calculate_new_stdprice(self, product):

        for rec in product.uom_standard_prices:
            new_price = 0
            margin = rec.price_margin / 100

            if self.price_filter == 'fixed':
                new_working_cost = self.price_change * ((100 + product.burden_percent) / 100)
                if self.cost_change_parent.update_burden and self.burden_change:
                    new_working_cost = self.price_change * ((100 + self.burden_change) / 100)
                if product.ppt_uom_id != rec.uom_id:
                    new_price = (product.ppt_uom_id._compute_price(new_working_cost, rec.uom_id) * (
                            (100 + product.categ_id.repacking_upcharge) / 100)) / (1 - margin)
                else:
                    new_price = new_working_cost / (1 - margin)


            else:
                new_working_cost = (product.standard_price * (100 + self.price_change) / 100) * (
                        (100 + product.burden_percent) / 100)
                if self.cost_change_parent.update_burden and self.burden_change:
                    new_working_cost = (product.standard_price * (100 + self.price_change) / 100) * (
                            (100 + self.burden_change) / 100)
                if product.ppt_uom_id != rec.uom_id:
                    new_price = (product.ppt_uom_id._compute_price(new_working_cost, rec.uom_id) * (
                            (100 + product.categ_id.repacking_upcharge) / 100)) / (1 - margin)
                else:
                    new_price = new_working_cost / (1 - margin)
            new_price = float_round(new_price, precision_digits=2)
            if rec.price != new_price:
                rec.with_context({'user': self.user_id and self.user_id.id, 'cost_cron': True}).price = new_price
