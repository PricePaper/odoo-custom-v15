# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_change_product_uom(self):
        wiz = self.env['change.product.uom'].create({'product_id': self.id})
        return {
                'name': 'Change Product UOM',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'change.product.uom',
                'target': 'new',
                'res_id': wiz.id,
                'context': {'default_product_id': self.id}
            }




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
