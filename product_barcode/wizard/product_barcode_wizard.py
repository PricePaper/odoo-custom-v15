from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductBarcode(models.TransientModel):
    _name = "product.barcode.wizard"

    product_id = fields.Many2one('product.product', string="Product Variants")
    product_tmpl_id = fields.Many2one('product.template', string="Product Name")
    supplier_id = fields.Many2one('product.supplierinfo', string="Supplier Name")
    product_barcode = fields.Char(string="Barcode")
    barcode_search = fields.Char(string="Barcode")

    def _onchange_product_barcode(self):
        if self.product_barcode:
            if self.product_id and self.supplier_id:
                barcode = self.env['product.barcode'].search([('product_barcode', '=', self.product_barcode)])
                if barcode:
                    raise ValidationError(_('Barcode already exist for product %s' % (barcode.product_id.name)))
                values = {
                    'product_id': self.product_id.id,
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'supplier_id': self.supplier_id.id,
                    'product_barcode': self.product_barcode
                    }
                self.env['product.barcode'].create(values)
                name = self.product_id.name
                self.product_id = False
                self.supplier_id = False
                self.product_barcode = False


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
                        'message': "Bacode Doesn't Exist",
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

    def apply_barcode(self):
        self._onchange_product_barcode()
        action = self.env['ir.actions.act_window']._for_xml_id('product_barcode.product_barcode_wizard')
        return action
