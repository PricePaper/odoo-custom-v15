# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_uom_ref_id = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True, related='product_id.ppt_uom_id')
    quantity_onhand = fields.Float('Quantity',
                                   help='Quantity of products in this quant, in the default unit of measure of the product',
                                   readonly=True, digits='Product Unit of Measure', compute='_compute_quantity_onhand',
                                   )
    inventory_quantity_mod = fields.Float(
        'Counted Quantity', digits='Product Unit of Measure',
        help="The product's counted quantity.")
    inventory_diff_quantity_mod = fields.Float(
        'Difference', compute='_compute_inventory_diff_quantity_mod', store=True,
        help="Indicates the gap between the product's theoretical quantity and its counted quantity.",
        readonly=True, digits='Product Unit of Measure')

    @api.depends('quantity')
    def _compute_quantity_onhand(self):
        for quant in self:
            if quant.product_uom_ref_id:
                quant.quantity_onhand = quant.product_uom_id._compute_quantity(quant.quantity, quant.product_uom_ref_id,
                                                                               rounding_method='HALF-UP')
            else:
                quant.quantity_onhand = 0

    @api.onchange('inventory_quantity_mod')
    def onchange_inventory_quantity_mod(self):
        if self.product_uom_ref_id:
            self.inventory_quantity = self.product_uom_ref_id._compute_quantity(self.inventory_quantity_mod,
                                                                                self.product_uom_id,
                                                                                rounding_method='HALF-UP')

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
        """
        fields = super(StockQuant, self)._get_inventory_fields_write()
        fields.extend(['inventory_quantity_mod', 'inventory_diff_quantity_mod'])
        return fields

    @api.depends('inventory_quantity_mod')
    def _compute_inventory_diff_quantity_mod(self):
        for quant in self:
            quant.inventory_diff_quantity_mod = quant.inventory_quantity_mod - quant.quantity_onhand

    def action_set_inventory_quantity_to_zero(self):
        self.inventory_quantity_mod = 0
        # self.inventory_diff_quantity_mod = 0
        super().action_set_inventory_quantity_to_zero()

    def action_set_inventory_quantity(self):
        res = super(StockQuant, self).action_set_inventory_quantity()
        if not res:
            for quant in self:
                quant.inventory_quantity_mod = quant.quantity_onhand

        return res

    def action_apply_inventory(self):
        res = super(StockQuant, self).action_apply_inventory()
        if not res:
            self.inventory_quantity_mod = 0
        return res


