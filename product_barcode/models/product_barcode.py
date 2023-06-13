from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductBarcode(models.Model):
    _name = 'product.barcode'

    product_id = fields.Many2one('product.product', string="Product")
    product_tmpl_id = fields.Many2one('product.template', string="Product Template")
    supplier_id = fields.Many2one('product.supplierinfo', string="Supplier")
    product_barcode = fields.Char(string="Product Barcode", copy=False)

    @api.constrains('product_barcode')
    def _check_product_barcode(self):
        """
        unique value for product barcode
        """

        barcode = self.env['product.barcode'].search([('product_barcode', '=', self.product_barcode), ('id', '!=', self.id)])
        if barcode:
            raise ValidationError('Barcode already exist')

    def action_remove(self):
        """
        Remove record
        """
        for rec in self:
            rec.unlink()
