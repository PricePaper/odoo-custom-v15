# -*- coding: utf-8 -*-
#todo starts from here
from odoo import models, fields, registry, api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, AccessError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    storage_contract_po = fields.Boolean(compute='_compute_storage_contract_po', store=True, string='Storage Contract PO')
    sale_order_ids = fields.Many2many('sale.order', 'Sale orders', compute="_get_sale_order", search="search_sale_order")
    is_make2order_po = fields.Boolean('Is make2order PO')

    @api.depends('order_line.sale_line_id')
    def _compute_sale_order(self):
        self.sale_order_ids = self._get_sale_orders()

    def search_sale_order(self, operator, value):
        if value == False:
            po = self.env['purchase.order.line'].search([('sale_line_id', '=', value)]).mapped('order_id')
            return [('id', operator, po.ids)]
        po = self.env['sale.order'].serach([('id', operator, value)])._get_purchase_orders()
        return [('id', 'in', po.ids)]


    @api.depends('order_line', 'order_line.sale_line_id')
    def _compute_storage_contract_po(self):
        for order in self:
            is_storage_contract = order.order_line.mapped('sale_line_id.order_id.storage_contract')
            if is_storage_contract and all(is_storage_contract):
                order.storage_contract_po = True
                continue
            order.storage_contract_po = False

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        storage_contract = self.mapped('order_line.sale_order_id').filtered(lambda s: s.storage_contract)
        if storage_contract:
            #todo check storage contract satte changes
            storage_contract.write({'sc_po_done': False, 'state': 'sale'})
        return res

    def button_draft(self):
        res = super(PurchaseOrder, self).button_draft()
        storage_contract = self.order_line.mapped('sale_order_id').filtered(lambda s: s.storage_contract)
        if storage_contract:
            storage_contract.write({'sc_po_done': True})
        return res

    def button_confirm(self):
        """
        cancel all other RFQ under the same purchase agreement
        """
        #todo it may make issues in maketoorder buy oirders relation is not stable

        self.mapped('order_line.sale_order_id').write({'state': 'ordered'})
        return super(PurchaseOrder, self).button_confirm()



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super()._prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values, po)
        if values.get('sale_line_id'):
            sale_line = self.env['sale.order.line'].browse(values.get('sale_line_id'))
            if sale_line.order_id.storage_contract:
                res['sale_line_id'] = sale_line.id
        elif values.get('move_dest_ids') and values.get('move_dest_ids').sale_line_id and values.get('move_dest_ids').sale_line_id.order_id.storage_contract:
            res['sale_line_id'] = values.get('move_dest_ids').sale_line_id.id
        input((res,'9999999999999999999999',values.get('sale_line_id'),'\n\n', values.get('move_dest_ids').sale_line_id))
        return res
PurchaseOrderLine()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
