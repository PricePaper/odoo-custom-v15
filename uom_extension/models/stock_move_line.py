# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    ppt_product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure',
                    readonly=True, related='product_id.ppt_uom_id')
    quantity_done = fields.Float('Quantity', readonly=True,
                    digits='Product Unit of Measure', compute='_compute_ppt_quantity_done')

    @api.depends('qty_done')
    def _compute_ppt_quantity_done(self):
        for line in self:
            if line.ppt_product_uom_id:
                line.quantity_done = line.product_uom_id._compute_quantity(line.qty_done, line.ppt_product_uom_id,
                                                                               rounding_method='HALF-UP')
            else:
                line.quantity_done = line.qty_done
