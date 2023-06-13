# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.tools import float_round


class ChangeProductUom(models.TransientModel):
    _name = 'change.product.uom'
    _description = 'Change Product UOM'

    product_id = fields.Many2one('product.product', string='Old Product')
    new_name = fields.Char('Name')
    new_default_code = fields.Char('Internal reference')
    new_uom = fields.Many2one('uom.uom', string='New UOM')
    new_sale_uoms = fields.Many2many('uom.uom', 'change_product_uom_rel', 'change_id', 'uom_id', string='New Sale UOMS')
    new_cost = fields.Float(string='Cost', digits='Product Price')
    volume = fields.Float(string='Volume')
    weight = fields.Float(string='Weight')
    duplicate_pricelist = fields.Boolean(string='Copy Pricelist')
    is_alternate_product = fields.Boolean(string='Add the new product to the old products Alternate Products?')
    is_supercede_product = fields.Boolean(string='Supercede old product with the new product?')

    @api.onchange('new_default_code')
    def _onchange_default_code(self):
        if not self.new_default_code:
            return

        domain = [('default_code', '=', self.new_default_code)]
        if self.env['product.product'].search(domain, limit=1):
            return {'warning': {
                'title': _("Note:"),
                'message': _("The Internal Reference '%s' already exists.", self.new_default_code),
            }}

    def create_duplicate_product(self):
        default_vals = {
            'name': self.new_name,
            'default_code': self.new_default_code,
            'standard_price': self.new_cost,
            'uom_id': self.new_uom.id,
            'uom_po_id': self.new_uom.id,
            'sale_ok': False,
            'weight': self.weight,
            'volume': self.volume
        }
        res = self.product_id.with_context(from_change_uom=True).copy(default=default_vals)
        res.sale_uoms = [(5, _, _)]
        res.sale_uoms = self.new_sale_uoms
        price_rec = self.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == self.product_id.uom_id)
        price = 0
        if price_rec:
            for uom in res.sale_uoms:
                price = float_round(price_rec[0].price * (uom.ratio / self.product_id.uom_id.ratio ), precision_digits=2)
                vals = {'product_id': res.id,
                        'uom_id': uom.id,
                        'price': price}
                self.env['product.standard.price'].create(vals)
        else:
            res.job_queue_standard_price_update()
        standard_price_days = self.env.user.company_id.standard_price_config_days or 75
        res.standard_price_date_lock = date.today() + relativedelta(days=standard_price_days)
        if self.duplicate_pricelist:
            lines = self.env['customer.product.price'].search([('product_id', '=', self.product_id.id)])

            for line in lines:
                default_1 = {'product_id': res.id}
                if line.product_uom == line.product_id.uom_id:
                    new_price = line.product_uom._compute_price(line.price, res.uom_id)
                    default_1['price'] = new_price
                    default_1['product_uom'] = res.uom_id.id
                    line.copy(default=default_1)
                elif line.product_uom in res.sale_uoms:
                    product = line.product_id
                    old_working_cost = product.cost
                    old_list_price = line.price
                    if product.uom_id != line.product_uom:
                        old_working_cost = product.uom_id._compute_price(product.cost, line.product_uom) * (
                                    (100 + product.categ_id.repacking_upcharge) / 100)
                    margin = (old_list_price - old_working_cost) / old_list_price
                    new_working_cost = res.cost

                    if res.uom_id != line.product_uom:
                        new_working_cost = res.uom_id._compute_price(new_working_cost, line.product_uom) * ((100 + res.categ_id.repacking_upcharge) / 100)

                    new_price = float_round(new_working_cost / (1 - margin), precision_digits=2)
                    default_1['price'] = new_price
                    line.copy(default=default_1)
        if self.is_alternate_product:
            new_ids = self.product_id.same_product_ids.ids
            if new_ids:
                new_ids.append(res.id)
            else:
                new_ids = [res.id]
            self.product_id.write({'same_product_ids': new_ids})
        if self.is_supercede_product:
            res.write({'superseded': [(0, 0, {'old_product': self.product_id.id, 'product_child_id': res.id})]})
        return {
            'name': 'Product Variants',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('product.product_normal_form_view').id,
            'res_model': 'product.product',
            'res_id': res.id,
        }
