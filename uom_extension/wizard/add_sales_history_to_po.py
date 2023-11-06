# -*- coding: utf-8 -*-

from odoo import api, models, _

class AddSaleHistoryPoLine(models.TransientModel):
    _inherit = 'add.sale.history.po.line'


    @api.depends('product_id')
    def _compute_op_min_max_days(self):
        """
        compute the min op value, max op value.
        min forecast days, max forecast days
        """
        for line in self:
            if line.product_id:
                line.op_max = line.product_id.orderpoint_ids and line.product_id.orderpoint_ids[0].product_max_qty_mod or 0
                line.op_min = line.product_id.orderpoint_ids and line.product_id.orderpoint_ids[0].product_min_qty_mod or 0
                po = self._context.get('active_id', False) and self.env['purchase.order'].browse(self._context.get('active_id', False)) or False
                if po:
                    vendor = po.partner_id
                    seller_rec = self.env['product.supplierinfo'].search([('name', '=', vendor.id), ('product_id', '=', line.product_id.id)], limit=1)

                    delay_days_min = 0
                    if seller_rec:
                        delay_days_min = seller_rec.delay
                    if not delay_days_min:
                        delay_days_min = vendor.delay

                    delay_days_max = delay_days_min + vendor.order_freq
                    line.forecast_days_min = delay_days_min
                    line.forecast_days_max = delay_days_max

    @api.depends('product_id')
    def _calc_qty_available(self):
        """
        compute on hand quantity in system to purchase units
        """
        for line in self:
            product_purchase_unit = line.product_id.uom_po_id
            changed_uom_qty = line.product_id.ppt_uom_id._compute_quantity(line.product_id.quantity_available, product_purchase_unit)
            changed_incoming_qty = line.product_id.ppt_uom_id._compute_quantity(line.product_id.incoming_quantity, product_purchase_unit)
            line.product_oh_qty = changed_uom_qty
            line.product_ip_qty = changed_incoming_qty
