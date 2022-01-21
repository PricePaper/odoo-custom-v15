# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, AccessError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    storage_contract_po = fields.Boolean(compute='_compute_storage_contract_po', store=True, string='Storage Contract PO')

    @api.depends('order_line', 'order_line.sale_line_id')
    def _compute_storage_contract_po(self):
        for order in self:
            out = order.order_line.mapped('sale_line_id.order_id.storage_contract')
            if out and all(out):
                order.storage_contract_po = True
            else:
                order.storage_contract_po = False

    def button_cancel(self):
        result = super(PurchaseOrder, self).button_cancel()
        sale = self.mapped('order_line.sale_order_id').filtered(lambda s: s.storage_contract)
        if sale:
            sale.write({'sc_po_done': False, 'state': 'sale'})
        return result

    def button_draft(self):
        res = super(PurchaseOrder, self).button_draft()
        sale = self.order_line.mapped('sale_order_id').filtered(lambda s: s.storage_contract)
        if sale:
            sale.write({'sc_po_done': True})
        return res

    def button_confirm(self):
        """
        cancel all other RFQ under the same purchase agreement
        """
        self.mapped('order_line.sale_order_id').write({'state': 'ordered'})
        return super(PurchaseOrder, self).button_confirm()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
