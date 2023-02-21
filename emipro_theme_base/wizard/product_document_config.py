"""
@author: Emipro Technologies Pvt. Ltd.
"""
from odoo import models, fields


class ProductDocumentConfig(models.TransientModel):
    """
    Class to handel Product Document Wizard
    """
    _name = 'product.document.config'
    _description = "Product Document Configuration Wizard"

    document_id = fields.Many2one('ir.attachment', string="Document")
    product_ids = fields.Many2many('product.template', 'product_config_wizard')
    temp_product_ids = fields.Many2many('product.template', 'temp_product_config_wizard')

    def assign_product_document(self):
        """
        assign document to products
        @return:
        """
        remove_doc_products = self.temp_product_ids - self.product_ids
        # remove the document in product
        for product in remove_doc_products:
            product.document_ids = [(3, self.document_id.id)]
        # add document to product
        for product_id in self.product_ids:
            product_id.document_ids = [(4, self.document_id.id)]
