# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PickingPendingProduct(models.Model):
    _name = 'picking.pending.product'
    _description = 'Batch Picking Pending Product'


    total = fields.Integer(string='Total')
    pending = fields.Integer(string='Pending')
    product_id = fields.Many2one('product.product', string='Product')
    batch_id = fields.Many2one('stock.picking.batch', string='Batch')

    @api.multi
    def open_pickings(self):
        pickings = []
        for rec in self:
            for picking in rec.batch_id.picking_ids:
                if self.product_id in picking.move_ids_without_package.mapped('product_id'):
                    pickings.append(picking.id)
        list_id = self.env.ref('stock.vpicktree').id
        form_id = self.env.ref('stock.view_picking_form').id
        res = {
            "type": "ir.actions.act_window",
            "name" : "Pickings With Pending Product",
            "res_model": "stock.picking",
            "views": [[list_id, "tree"], [form_id, "form"]],
            "context": {},
            "domain":[('id', 'in', pickings)],
            "target": "current",
        }
        return res



PickingPendingProduct()
