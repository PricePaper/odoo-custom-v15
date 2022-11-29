from odoo import api, fields, models


class ProductBarcode(models.TransientModel):
    _name = "product.barcode.wizard"
    _inherit = ['barcodes.barcode_events_mixin']

    product_id = fields.Many2one('product.product', string="Product Variants")
    product_tmpl_id = fields.Many2one('product.template', string="Product Name")
    supplier_id = fields.Many2one('product.supplierinfo', string="Supplier Name")
    product_barcode = fields.Char(string="Barcode")
    barcode_search = fields.Char(string="Barcode")


    def on_barcode_scanned(self, barcode):
        """
        creating records for product barcode
        """

        if barcode:
            product_barcode = self.env['product.barcode'].search([('product_barcode', '=', self.product_barcode)])
            if product_barcode:
                return {'warning': {
                    'title': "Warning",
                    'message': 'Barcode already exist for product %s' % (product_barcode.product_id.name),
                    }
                    }

            if self.product_id and self.supplier_id:
                values = {
                    'product_id': self.product_id.id,
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'supplier_id': self.supplier_id.id,
                    'product_barcode': barcode
                    }
                self.env['product.barcode'].create(values)
                name = self.product_id.name
                self.product_id = False
                self.supplier_id = False
                self._barcode_scanned = False
                return {'warning': {
                    'title': "Barcode Added",
                    'message': 'Barcode added for product %s' % (name),
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

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Assigning corresponding value for the product_template
        """
        if self.product_id:
            self.product_tmpl_id = self.product_id.product_tmpl_id
        else:
            self.product_tmpl_id = False
