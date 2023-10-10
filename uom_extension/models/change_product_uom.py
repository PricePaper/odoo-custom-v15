# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.tools import float_round


class ChangeProductUom(models.TransientModel):
    _inherit = 'change.product.uom'

    def action_change_uom(self):

        product = self.product_id
        product.sale_uoms = [(5, _, _)]
        product.sale_uoms = self.new_sale_uoms
        product.ppt_uom_id = self.new_uom.id
        price_rec = self.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == self.product_id.ppt_uom_id)
        price = 0
        if price_rec:
            price = price_rec[0].price
        self.product_id.uom_standard_prices.unlink()
        if price_rec:
            for uom in product.sale_uoms:
                price = float_round(price * (uom.ratio / self.product_id.ppt_uom_id.ratio),
                                    precision_digits=2)
                vals = {'product_id': product.id,
                        'uom_id': uom.id,
                        'price': price}
                self.env['product.standard.price'].create(vals)
        else:
            product.job_queue_standard_price_update()
        standard_price_days = self.env.user.company_id.standard_price_config_days or 75
        product.standard_price_date_lock = date.today() + relativedelta(days=standard_price_days)

        if self.duplicate_pricelist:
            new_uom_ids = self.mapper_ids.mapped('new_uom_id')
            if not all(mapper_id.new_uom_id for mapper_id in self.mapper_ids):
                raise ValidationError('Please add the New UOMs for price list mapping')

            lines = self.env['customer.product.price'].search([('product_id', '=', self.product_id.id)])
            for map_id in self.mapper_ids:
                if map_id.old_uom_id == map_id.new_uom_id:
                    continue
                for line in lines.filtered(lambda r: r.product_uom == map_id.old_uom_id):
                    default_1 = {'product_id': product.id, 'product_uom': map_id.new_uom_id.id}
                    if self.maintain_price_ratio:
                        new_price = map_id.old_uom_id._compute_price(line.price, map_id.new_uom_id)
                        default_1['price'] = new_price
                    else:
                        default_1['price'] = line.price
                    line.copy(default=default_1)
