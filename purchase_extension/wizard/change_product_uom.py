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
    # is_alternate_product = fields.Boolean(string='Add the new product to the old products Alternate Products?')
    # is_supercede_product = fields.Boolean(string='Supercede old product with the new product?')
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
        pass 


class SaleUomMapper(models.TransientModel):
    _name = 'sale.uom.mapper'
    _description = 'Map Sale Uom'

    change_id = fields.Many2one('change.product.uom', string='Change Id')
    old_uom_id = fields.Many2one('uom.uom', string='Old Uom')
    new_uom_id = fields.Many2one('uom.uom', string='New Uom')
