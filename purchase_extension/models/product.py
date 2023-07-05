# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_change_product_uom(self):
        return {
            'name': 'Change Product UOM',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'change.product.uom',
            'target': 'new',
            'context': {'default_product_id': self.id,}
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
