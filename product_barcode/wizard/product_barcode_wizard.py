from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductBarcode(models.TransientModel):
    _name = "product.barcode.wizard"

    product_id = fields.Many2one('product.product', string="Product Variants")
    product_tmpl_id = fields.Many2one('product.template', string="Product Name")
    supplier_id = fields.Many2one('product.supplierinfo', string="Supplier Name")
    product_barcode = fields.Char(string="Barcode")
    barcode_search = fields.Char(string="Barcode")

    def add_product_barcode(self):
        """
        Creating values in product_barcode model
        """
        for product in self:
            values = {
                'product_id': product.product_id.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'supplier_id': product.supplier_id.id,
                'product_barcode': product.product_barcode
            }
            barcode = self.env['product.barcode'].create(values)


    @api.onchange('product_barcode')
    def _onchange_product_barcode(self):
        """
        Raise error message whether the barcode already exist
        """
        if self.product_barcode:
            barcode = self.env['product.barcode'].search([('product_barcode', '=', self.product_barcode)])
            if barcode:
                return {'warning': {
                        'title': "Warning",
                        'message': 'Barcode already exist for product %s' % (barcode.product_id.name),
                        }
                        }


    @api.onchange('barcode_search')
    def _onchange_product_search(self):
        """
        search barcode on onchange
        """
        if self.barcode_search:
            barcode = self.env['product.barcode'].search([('product_barcode', '=', self.barcode_search)])
            if barcode:
                self.product_id = barcode.product_id
                self.product_tmpl_id = barcode.product_tmpl_id
                self.supplier_id = barcode.supplier_id
            else:
                self.product_id = False
                self.product_tmpl_id = False
                self.supplier_id = False
                self.barcode_search = False
                return {'warning': {
                        'title': "Warning",
                        'message': "Product Doesn't Exist",
                        }
                        }
