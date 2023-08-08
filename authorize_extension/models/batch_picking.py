# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    def action_confirm(self):
        self.ensure_one()
        pickings_on_hold = self.picking_ids.filtered(lambda r:r.is_payment_hold == True)
        if pickings_on_hold:
            msg = ''
            order_names = ''
            orders = pickings_on_hold.mapped('sale_id').filtered(lambda r: r.is_transaction_pending or r.is_transaction_error)
            for order in  orders:
                order_names = order.name + '(' + order.partner_id.name + '),'
            if orders:
                msg += 'Order '+ order_names + ' has Transaction Issues please contact Accounting Manager\n'
            orders = pickings_on_hold.mapped('sale_id').filtered(lambda r:r.credit_hold_after_confirm or r.is_transaction_error)
            order_names = ''
            for order in  orders:
                order_names = order.name + '(' + order.partner_id.name + '),'
            if orders:
                msg += 'Order '+ order_names + ' is in Credit hold please contact Credit Manager'
            if not msg:
                msg = 'Some pickings are in Hold State'


            raise ValidationError(msg)
        res = super(StockPickingBatch, self).action_confirm()
        return res

    def set_in_truck(self):
        res = super(StockPickingBatch, self).set_in_truck()
        msg = ''
        for picking in self.picking_ids.filtered(lambda r:r.is_payment_hold == True):
            order = picking.sale_id
            if order.is_transaction_pending:
                msg += '\nOrder:'+ order.name + 'Customer: '+ order.partner_id.name + ' is in Transaction Pending state'
            if order.is_transaction_error:
                msg += '\nOrder:'+ order.name + 'Customer: '+ order.partner_id.name + ' is in Transaction Pending state'
            if order.credit_hold_after_confirm:
                msg += '\nOrder:'+ order.name + 'Customer: '+ order.partner_id.name + ' is in Credit Hold state'
        if msg:
            msg += '\n\nPlease contact Accounting Manager for Transaction related issue.\nContact Credit Manager for credit hold issue'
            view_id = self.env.ref('authorize_extension.view_batch_warning_wizard').id
            return {
                'name': 'Batch Warning',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'batch.warning.wizard',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'context': {'default_warning_message': msg},
                'target': 'new'
            }
        return res
