# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.tools import float_round


class ChangeProductUom(models.TransientModel):
    _inherit = 'change.product.uom'

    new_po_uom = fields.Many2one('uom.uom', string='New Purchase UOM')

    def action_change_uom(self):

        product = self.product_id
        old_uom = product.ppt_uom_id
        product.sale_uoms = [(5, _, _)]
        product.sale_uoms = self.new_sale_uoms
        product.ppt_uom_id = self.new_uom.id
        product.uom_po_id = self.new_po_uom.id


        for price_rec in self.product_id.uom_standard_prices:
            mapper_uom = self.mapper_ids.filtered(lambda r: r.old_uom_id == price_rec.uom_id)
            if self.maintain_price_ratio:
                new_price = mapper_uom.old_uom_id._compute_price(price_rec.price, mapper_uom.new_uom_id)
                price_rec.write({'uom_id': mapper_uom.new_uom_id.id,
                                 'price': new_price})
            else:
                price_rec.write({'uom_id': mapper_uom.new_uom_id.id})

        if not self.product_id.uom_standard_prices:
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

    def create_duplicate_product(self):
        default_vals = {
            'name': self.new_name,
            'default_code': self.new_default_code,
            'standard_price': self.new_cost,
            'ppt_uom_id': self.new_uom.id,
            'uom_po_id': self.new_po_uom.id,
            'sale_ok': True,
            'weight': self.weight,
            'volume': self.volume
        }
        res = self.product_id.with_context(from_change_uom=True).copy(default=default_vals)
        res.sale_uoms = [(5, _, _)]
        res.sale_uoms = self.new_sale_uoms

        return {
            'name': 'Product Variants',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('product.product_normal_form_view').id,
            'res_model': 'product.product',
            'res_id': res.id,
        }
