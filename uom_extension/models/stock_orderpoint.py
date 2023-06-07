# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    product_min_qty_mod = fields.Float(
        'Min Quantity', digits='Product Unit of Measure', required=True, default=0.0,
        help="When the virtual stock goes below the Min Quantity specified for this field, Odoo generates"
             "a procurement to bring the forecasted quantity to the Max Quantity.", store=True)
    product_max_qty_mod = fields.Float('Max Quantity', digits='Product Unit of Measure', required=True, default=0.0,
                                   help="When the virtual stock goes below the Min Quantity, Odoo generates "
                                        "a procurement to bring the forecasted quantity to the Quantity specified as Max Quantity.",
                                   )
    product_min_qty = fields.Float('Min Quantity', digits='Product Unit of Measure', required=True, default=0.0,
                                   help="When the virtual stock goes below the Min Quantity specified for this field, Odoo generates "
                                        "a procurement to bring the forecasted quantity to the Max Quantity.", compute='_compute_min_max_quantities', store=True
                                   )
    product_max_qty = fields.Float('Max Quantity', digits='Product Unit of Measure', required=True, default=0.0,
                                   help="When the virtual stock goes below the Min Quantity, Odoo generates "
                                        "a procurement to bring the forecasted quantity to the Quantity specified as Max Quantity.",
                                   compute='_compute_min_max_quantities', store=True)
    product_ppt_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure', related='product_id.ppt_uom_id')
    product_ppt_uom_name = fields.Char(string='Product unit of measure label', related='product_ppt_uom.display_name',
                                   readonly=True)

    @api.depends('product_min_qty_mod')
    def _compute_min_max_quantities(self):
        for op in self:
            op.product_min_qty = op.product_ppt_uom._compute_quantity(op.product_min_qty_mod, op.product_uom,
                                                                      rounding_method='HALF-UP')
            op.product_max_qty = op.product_ppt_uom._compute_quantity(op.product_max_qty_mod, op.product_uom,
                                                                      rounding_method='HALF-UP')

