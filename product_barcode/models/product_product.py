from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode_ids = fields.One2many('product.barcode', 'product_id', string='Barcode')

    def action_add_barcode(self):
        """
        Add barcode using wizard
        """

        action = self.env['ir.actions.actions']._for_xml_id('product_barcode.product_barcode_wizard')
        action.update({
            'views': [[False, 'form']],
            'context': {'default_product_id': self.id,
                        'default_product_tmpl_id': self.product_tmpl_id.id}
        })

        return action
