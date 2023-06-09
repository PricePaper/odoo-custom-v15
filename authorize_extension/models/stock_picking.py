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

class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, vals):
        if vals.get('state', False):
            if self.picking_id.is_payment_hold:
                order = self.picking_id.sale_id
                if order:
                    if order.is_transaction_pending or order.is_transaction_error:
                        raise UserError('You can not change the state of %s. Payment Transaction is in hold or error state please contact Accountant'%(self.picking_id.name))
                    if order.credit_hold_after_confirm:
                        raise UserError('You can not change the state of %s. Sale order is in credit hold state please contact Credit manager'%(self.picking_id.name))
        return super().write(vals)
