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
    mapper_ids = fields.One2many('sale.uom.mapper', 'change_id', string='Sale Uom Mapping')
    maintain_price_ratio = fields.Boolean(string='Maintain price ratio')

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

    def default_get(self, vals):
        product = self.env['product.product'].browse(self._context.get('active_id'))
        res = super(ChangeProductUom, self).default_get(vals)
        res['mapper_ids'] = [(0, 0, {'old_uom_id': sale_uom.id}) for sale_uom in product.sale_uoms]
        return res

    @api.onchange('duplicate_pricelist')
    def onchange_duplicate_pricelist(self):
        if not self.duplicate_pricelist:
            self.maintain_price_ratio = False
        else:
            self.maintain_price_ratio = True

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
                price = float_round(price_rec[0].price * (uom.ratio / self.product_id.uom_id.ratio),
                                    precision_digits=2)
                vals = {'product_id': res.id,
                        'uom_id': uom.id,
                        'price': price}
                self.env['product.standard.price'].create(vals)
        else:
            res.job_queue_standard_price_update()
        standard_price_days = self.env.user.company_id.standard_price_config_days or 75
        res.standard_price_date_lock = date.today() + relativedelta(days=standard_price_days)

        if self.duplicate_pricelist:
            new_uom_ids = self.mapper_ids.mapped('new_uom_id')
            if not all(mapper_id.new_uom_id for mapper_id in self.mapper_ids):
                raise ValidationError('Please add the New UOMs for price list mapping')

            lines = self.env['customer.product.price'].search([('product_id', '=', self.product_id.id)])
            for map_id in self.mapper_ids:
                for line in lines.filtered(lambda r: r.product_uom == map_id.old_uom_id):
                    default_1 = {'product_id': res.id, 'product_uom': map_id.new_uom_id.id}
                    if self.maintain_price_ratio:
                        new_price = map_id.old_uom_id._compute_price(line.price, map_id.new_uom_id)
                        default_1['price'] = new_price
                    else:
                        default_1['price'] = line.price
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


class SaleUomMapper(models.TransientModel):
    _name = 'sale.uom.mapper'
    _description = 'Map Sale Uom'

    change_id = fields.Many2one('change.product.uom', string='Change Id')
    old_uom_id = fields.Many2one('uom.uom', string='Old Uom')
    new_uom_id = fields.Many2one('uom.uom', string='New Uom')




