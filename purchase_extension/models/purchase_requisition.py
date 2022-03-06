# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    supplier_ids = fields.Many2many('res.partner', string="Suppliers")

    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        suppliers = set()
        for requisition in self:
            suppliers |= set(requisition.line_ids.mapped(lambda rec: rec.product_id).mapped(
                lambda rec: rec.variant_seller_ids).mapped(lambda rec: rec.name.id))
            requisition.supplier_ids = [(6, 0, list(suppliers))]

    def action_in_progress(self):
        self.ensure_one()
        super(PurchaseRequisition, self).action_in_progress()
        purchase_order_obj = self.env['purchase.order']
        for supplier in self.supplier_ids:
            purchase_order_obj.create({'partner_id': supplier.id, 'requisition_id': self.id})._onchange_requisition_id()
