# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_payment_hold = fields.Boolean(string='Payment Hold', copy=False)

    def create_invoice(self):
        for picking in self:
            if picking.is_payment_hold:
                raise UserError('%s Delivery Order in hold state'%(picking.name))
        return super(StockPicking, self).create_invoice()

class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, vals):
        if vals.get('state', False):
            for move in self:
                if move.picking_id.is_payment_hold:
                    order = move.picking_id.sale_id
                    if order:
                        if order.is_transaction_pending or order.is_transaction_error:
                            raise UserError('%s is on hold or in error state, and the Truck Batch is confirmed. Please contact Sales'%(self.picking_id.name))
                        if order.credit_hold_after_confirm:
                            raise UserError('You can not change the state of %s. Sale order is in credit hold state please contact Credit manager'%(self.picking_id.name))
        return super().write(vals)
