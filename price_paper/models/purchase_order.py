# -*- coding: utf-8 -*-

from odoo import models, fields, registry, api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, AccessError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_cancel(self):
        result = super(PurchaseOrder, self).button_cancel()
        self.mapped('order_line.sale_order_id').write({'sc_po_done': False})
        return result

    @api.multi
    def button_confirm(self):
        """
        cancel all other RFQ under the same purchase agreement
        """
        self.mapped('order_line.sale_order_id').action_done()
        return super(PurchaseOrder, self).button_confirm()


PurchaseOrder()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
