# -*- coding: utf-8 -*-

from odoo import fields, models, api

#todo not used anywhere remove it before go live
class PickingPendingProduct(models.Model):
    _name = 'picking.pending.product'
    _description = 'Batch Picking Pending Product'

    total = fields.Integer(string='Total', compute='_compute_quantity')
    pending = fields.Integer(string='Pending', compute='_compute_quantity')
    product_id = fields.Many2one('product.product', string='Product')
    batch_id = fields.Many2one('stock.picking.batch', string='Batch')
    user_id = fields.Many2one('res.users', string='User')

    @api.depends('batch_id', 'product_id')
    def _compute_quantity(self):
        for rec in self:
            moves = rec.batch_id.picking_ids.mapped('move_ids_without_package').filtered(
                lambda move: move.product_id == rec.product_id and move.state != 'cancel')
            total = sum(moves.mapped('product_uom_qty'))
            reserved = sum(moves.mapped(lambda
                                            move: move.product_uom_qty if move.reserved_availability == 0 and move.state == 'done' else 0 if move.reserved_availability == 0 else move.reserved_availability))
            rec.total = total
            rec.pending = total - reserved

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
            "name": "Pickings With Pending Product",
            "res_model": "stock.picking",
            "views": [[list_id, "tree"], [form_id, "form"]],
            "context": {},
            "domain": [('id', 'in', pickings)],
            "target": "current",
        }
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
