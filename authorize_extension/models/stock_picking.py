# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_payment_hold = fields.Boolean(string='Payment Hold', copy=False)

class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, vals):
        if vals.get('state', False):
            if self.picking_id.is_payment_hold:
                raise UserError('You can not change the state of %s. Payment Transaction is in hold state please contact Accountant'%(self.picking_id.name))
        return super().write(vals)
