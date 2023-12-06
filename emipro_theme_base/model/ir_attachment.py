"""
@author: Emipro Technologies Pvt. Ltd.
"""
# -*- coding: utf-8 -*-
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    """
    Inherit attachment for product document
    """
    _inherit = 'ir.attachment'

    is_product_document = fields.Boolean('Product Document')

    def config_product_document(self):
        """
        action call for wizard to configure product
        @return:
        """
        products = self.env['product.template'].search([('document_ids.id', '=', self.id)])
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'product.document.config',
            'name': "Assign/Unassign to Products",
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_document_id':self.id, 'default_product_ids':products.ids, 'default_temp_product_ids':products.ids},
        }
        return action

    def _cron_product_document_process(self):
        _logger.info("Product Documents Updated Working")
        products = self.env['product.template'].search([])
        products.document_ids.write({'is_product_document':True,'public':True})
        _logger.info("Product Documents Updated")
