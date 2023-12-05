# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_change_product_stock(self):
        return {
            'name': 'Get Product Stock',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'change.product.stock',
            'target': 'new',
            'context': {'default_dest_product_id': self.id}
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
