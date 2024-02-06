# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_uom_ref_id = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True, related='product_id.ppt_uom_id')
    quantity_onhand = fields.Float('Quantity',
                                   help='Quantity of products in this quant, in the default unit of measure of the product',
                                   readonly=True, digits='Product Unit of Measure', compute='_compute_quantity_onhand', store=True
                                   )
    inventory_quantity_mod = fields.Float(
        'Counted Quantity', digits='Product Unit of Measure',
        help="The product's counted quantity.")
    inventory_diff_quantity_mod = fields.Float(
        'Difference', compute='_compute_inventory_diff_quantity_mod', store=True,
        help="Indicates the gap between the product's theoretical quantity and its counted quantity.",
        readonly=True, digits='Product Unit of Measure')
    ppt_available_qty = fields.Float(
        'Available Quantity',
        help="On hand quantity which hasn't been reserved on a transfer, in the default unit of measure of the product",
        compute='_compute_ppt_available_quantity', digits='Product Unit of Measure')
    lot_uom_id = fields.Many2one('uom.uom', 'Lot UOM', readonly=True, compute='_compute_lot_uom')
    lot_qty = fields.Float('Lot UOM Qty',
                                   readonly=True, digits='Product Unit of Measure', compute='_compute_lot_uom'
                                   )

    def _compute_lot_uom(self):
        for quant in self:
            purchase = quant.lot_id.purchase_order_ids
            if purchase:
                uom = purchase.order_line.filtered(lambda r: r.product_id == quant.product_id and r.qty_received > 0).product_uom
                if uom:
                    quant.lot_uom_id = uom[0].id
                    quant.lot_qty = quant.product_uom_id._compute_quantity(quant.quantity - quant.reserved_quantity,
                                                                                   uom, rounding_method='HALF-UP')
                    continue
            quant.lot_uom_id = False
            quant.lot_qty = 0.0

    @api.depends('quantity', 'reserved_quantity')
    def _compute_ppt_available_quantity(self):
        for quant in self:
            quant.ppt_available_qty = quant.product_uom_id._compute_quantity(quant.quantity - quant.reserved_quantity,
                                                                           quant.product_uom_ref_id,
                                                                           rounding_method='HALF-UP')

    @api.depends('quantity')
    def _compute_quantity_onhand(self):
        for quant in self:
            if quant.product_uom_ref_id:
                quant.quantity_onhand = quant.product_uom_id._compute_quantity(quant.quantity, quant.product_uom_ref_id,
                                                                               rounding_method='HALF-UP')
            else:
                quant.quantity_onhand = quant.quantity

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

    @api.depends('company_id', 'location_id', 'owner_id', 'product_id', 'quantity')
    def _compute_value(self):
        """ For standard and AVCO valuation, compute the current accounting
        valuation of the quants by multiplying the quantity by
        the standard price. Instead for FIFO, use the quantity times the
        average cost (valuation layers are not manage by location so the
        average cost is the same for all location and the valuation field is
        a estimation more than a real value).
        """
        for quant in self:
            quant.currency_id = quant.company_id.currency_id
            # If the user didn't enter a location yet while enconding a quant.
            if not quant.location_id:
                quant.value = 0
                return
            if not quant.location_id._should_be_valued() or \
                    (quant.owner_id and quant.owner_id != quant.company_id.partner_id):
                quant.value = 0
                continue
            if quant.product_id.cost_method == 'fifo':
                quantity = quant.product_id.with_company(quant.company_id).quantity_svl
                if float_is_zero(quantity, precision_rounding=quant.product_id.uom_id.rounding):
                    quant.value = 0.0
                    continue
                average_cost = quant.product_id.with_company(quant.company_id).value_svl / quantity
                quant.value = quant.quantity_onhand * average_cost
            else:
                quant.value = quant.quantity * quant.product_id.with_company(quant.company_id).standard_price
